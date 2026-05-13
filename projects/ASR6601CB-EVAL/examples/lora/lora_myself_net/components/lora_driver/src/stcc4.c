#include "stcc4.h"

#include "lora_config.h"
#include "tremo_delay.h"
#include "tremo_gpio.h"
#include "tremo_i2c.h"
#include "tremo_rcc.h"
#include <stddef.h>
#include <stdio.h>

#define STCC4_I2C_ADDR             0x64
#define STCC4_I2C_WAIT_TIMEOUT     200000U
/* Wait after VDD stabilizes before sending the first STCC4 command. */
#define STCC4_POWER_ON_DELAY_MS    1000U
#define STCC4_MEASURE_WAIT_MS      5200U
#define STCC4_READ_WAIT_MS         5U

#define STCC4_CMD_START_CONTINUOUS 0x218B
#define STCC4_CMD_READ_MEASUREMENT 0xEC05

/* Track whether continuous measurement mode has already been started.
 * The sensor will NAK a repeated start command while already measuring. */
static bool s_continuous_started = false;

static bool stcc4_write_cmd_u16(uint16_t cmd);

static void stcc4_set_co2_en(bool enable)
{
    gpio_set_iomux(CONFIG_CO2_EN_GPIOX, CONFIG_CO2_EN_PIN, 0);
    gpio_init(CONFIG_CO2_EN_GPIOX, CONFIG_CO2_EN_PIN,
              enable ? GPIO_MODE_OUTPUT_PP_HIGH : GPIO_MODE_OUTPUT_PP_LOW);
    gpio_write(CONFIG_CO2_EN_GPIOX, CONFIG_CO2_EN_PIN,
               enable ? GPIO_LEVEL_HIGH : GPIO_LEVEL_LOW);
}

static void stcc4_i2c_prepare(void)
{
    i2c_config_t config;

    rcc_enable_peripheral_clk(RCC_PERIPHERAL_I2C0, true);
    rcc_enable_peripheral_clk(RCC_PERIPHERAL_GPIOA, true);

    gpio_set_iomux(CONFIG_RA08_I2C_GPIOX, CONFIG_RA08_I2C_SCL_PIN, 3);
    gpio_set_iomux(CONFIG_RA08_I2C_GPIOX, CONFIG_RA08_I2C_SDA_PIN, 3);

    i2c_config_init(&config);
    config.mode = I2C_MODE_MASTER;
    config.fifo_mode_en = false;
    config.settings.master.speed = I2C_SPEED_STANDARD;
    i2c_init(I2C0, &config);
    i2c_cmd(I2C0, true);
}

static bool stcc4_i2c_wait_flag(i2c_t *i2c, i2c_flag_t flag)
{
    uint32_t timeout = STCC4_I2C_WAIT_TIMEOUT;
    while ((i2c_get_flag_status(i2c, flag) != SET) && (timeout > 0U)) {
        timeout--;
    }
    return (timeout > 0U);
}

static uint8_t stcc4_crc8(const uint8_t *data, uint8_t len)
{
    uint8_t crc = 0xFF;
    uint8_t i;
    uint8_t b;

    for (i = 0; i < len; ++i) {
        crc ^= data[i];
        for (b = 0; b < 8; ++b) {
            crc = (crc & 0x80U) ? (uint8_t)((crc << 1) ^ 0x31U) : (uint8_t)(crc << 1);
        }
    }

    return crc;
}

static bool stcc4_write_cmd_u16(uint16_t cmd)
{
    i2c_master_send_start(I2C0, STCC4_I2C_ADDR, I2C_WRITE);
    i2c_clear_flag_status(I2C0, I2C_FLAG_TRANS_EMPTY);
    if (!stcc4_i2c_wait_flag(I2C0, I2C_FLAG_TRANS_EMPTY)) {
        i2c_master_send_stop(I2C0);
        return false;
    }

    i2c_send_data(I2C0, (uint8_t)((cmd >> 8) & 0xFF));
    i2c_clear_flag_status(I2C0, I2C_FLAG_TRANS_EMPTY);
    if (!stcc4_i2c_wait_flag(I2C0, I2C_FLAG_TRANS_EMPTY)) {
        i2c_master_send_stop(I2C0);
        return false;
    }

    i2c_send_data(I2C0, (uint8_t)(cmd & 0xFF));
    i2c_clear_flag_status(I2C0, I2C_FLAG_TRANS_EMPTY);
    if (!stcc4_i2c_wait_flag(I2C0, I2C_FLAG_TRANS_EMPTY)) {
        i2c_master_send_stop(I2C0);
        return false;
    }

    i2c_master_send_stop(I2C0);
    return true;
}

static bool stcc4_read_bytes(uint8_t *buf, uint8_t len)
{
    int i;

    i2c_master_send_start(I2C0, STCC4_I2C_ADDR, I2C_READ);
    i2c_clear_flag_status(I2C0, I2C_FLAG_TRANS_EMPTY);
    if (!stcc4_i2c_wait_flag(I2C0, I2C_FLAG_TRANS_EMPTY)) {
        printf("[STCC4] read address timeout\r\n");
        i2c_master_send_stop(I2C0);
        return false;
    }

    for (i = 0; i < len; ++i) {
        i2c_set_receive_mode(I2C0, (i == (len - 1)) ? I2C_NAK : I2C_ACK);
        if (!stcc4_i2c_wait_flag(I2C0, I2C_FLAG_RECV_FULL)) {
            printf("[STCC4] read byte %d timeout\r\n", i);
            i2c_master_send_stop(I2C0);
            return false;
        }
        buf[i] = i2c_receive_data(I2C0);
        i2c_clear_flag_status(I2C0, I2C_FLAG_RECV_FULL);
    }

    i2c_master_send_stop(I2C0);
    return true;
}

bool stcc4_init(void)
{
    s_continuous_started = false;
    stcc4_set_co2_en(true);
    delay_ms(STCC4_POWER_ON_DELAY_MS);
    stcc4_i2c_prepare();
    printf("[STCC4] init done, CO2_EN hold, waited %ums for STCC4 boot\r\n",
           (unsigned)STCC4_POWER_ON_DELAY_MS);
    return true;
}

bool stcc4_read_co2(uint16_t *co2_ppm)
{
    uint8_t meas[9];
    if (co2_ppm == NULL) {
        return false;
    }
    stcc4_set_co2_en(true);
    stcc4_i2c_prepare();
    /* Only send start_continuous_measurement once to avoid repeated-start NAK. */
    if (!s_continuous_started) {
        if (!stcc4_write_cmd_u16(STCC4_CMD_START_CONTINUOUS)) {
            printf("[STCC4] start_continuous NAK\r\n");
            return false;
        }
        s_continuous_started = true;
        printf("[STCC4] continuous measurement started\r\n");
    }
    delay_ms(STCC4_MEASURE_WAIT_MS);

    if (!stcc4_write_cmd_u16(STCC4_CMD_READ_MEASUREMENT)) {
        printf("[STCC4] read_measurement cmd NAK\r\n");
        return false;
    }
    printf("[STCC4] read_measurement cmd OK, reading %u bytes\r\n", (unsigned)sizeof(meas));

    delay_ms(STCC4_READ_WAIT_MS);

    if (!stcc4_read_bytes(meas, 9)) {
        printf("[STCC4] measurement read failed\r\n");
        return false;
    }
    if (stcc4_crc8(&meas[0], 2) != meas[2]) {
        printf("[STCC4] meas CRC0 err\r\n");
        return false;
    }
    if (stcc4_crc8(&meas[3], 2) != meas[5]) {
        printf("[STCC4] meas CRC1 err\r\n");
        return false;
    }
    if (stcc4_crc8(&meas[6], 2) != meas[8]) {
        printf("[STCC4] meas CRC2 err\r\n");
        return false;
    }
    *co2_ppm = (uint16_t)(((uint16_t)meas[0] << 8) | meas[1]);
    return true;
}
