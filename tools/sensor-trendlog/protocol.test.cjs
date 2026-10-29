const assert=require('node:assert/strict');
const {parse,Lines}=require('./protocol.js');
const sample='AT+SENSOR=B7180A12,2332,5627,65,390,0,13,-94,8';
const r=parse(sample,123);assert.equal(r.temperature,23.32);assert.equal(r.humidity,56.27);assert.equal(r.voltage,65);assert.equal(r.time,123);assert.equal(r.rssi,-94);
assert.equal(parse(sample.replace('2332','-123')).temperature,-1.23);
for(const bad of [sample+',9',sample.replace('2332','32768'),sample.replace(',65,',',-1,'),sample.replace('B7180A12','BAD'),sample.replace(',8',',128'),'debug'])assert.equal(parse(bad),null);
let result=[];const lines=new Lines(l=>result.push(l));lines.push(sample.slice(0,20));lines.push(sample.slice(20)+'\r');lines.push('\n'+sample+'\n'+sample);lines.flush();assert.deepEqual(result,[sample,sample,sample]);
console.log('PASS: conversion, signed values, invalid frames, split frames, CRLF and flush');
