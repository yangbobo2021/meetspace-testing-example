const fs=require('fs'),path=require('path');
const base=__dirname;
const {createInstrumenter}=require('./tools/node/node_modules/istanbul-lib-instrument');
const source=fs.readFileSync(path.resolve(base,'../../../../web/app.js'),'utf8');
const i=createInstrumenter({coverageGlobalScope:'globalThis',coverageGlobalScopeFunc:false,compact:false,produceSourceMap:true});
fs.writeFileSync(path.join(base,'instrumented-app.js'),i.instrumentSync(source,'web/app.js'));
fs.writeFileSync(path.join(base,'frontend-static-map.json'),JSON.stringify(i.lastFileCoverage(),null,2));
fs.writeFileSync(path.join(base,'frontend-source-map.json'),JSON.stringify(i.lastSourceMap(),null,2));
