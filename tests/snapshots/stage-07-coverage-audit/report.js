const fs=require('fs'),path=require('path'),base=__dirname;
const {createCoverageMap}=require('./tools/node/node_modules/istanbul-lib-coverage');
const map=createCoverageMap({'web/app.js':JSON.parse(fs.readFileSync(path.join(base,'frontend-static-map.json')))});
for(const f of fs.readdirSync(path.join(base,'javascript-data'))) {
 const doc=JSON.parse(fs.readFileSync(path.join(base,'javascript-data',f)));map.merge(doc.coverage);
}
const file=map.fileCoverageFor('web/app.js');
const result={file:'web/app.js',tool:'Istanbul',version:'6.0.3',summary:file.toSummary().data,uncovered_lines:file.getUncoveredLines().map(Number),missing_statements:[],missing_functions:[],missing_branches:[],raw:file.data};
for(const [id,n] of Object.entries(file.s))if(!n)result.missing_statements.push({id,location:file.statementMap[id]});
for(const [id,n] of Object.entries(file.f))if(!n)result.missing_functions.push({id,location:file.fnMap[id]});
for(const [id,counts] of Object.entries(file.b))counts.forEach((n,index)=>{if(!n)result.missing_branches.push({id,index,type:file.branchMap[id].type,condition:file.branchMap[id].loc,location:file.branchMap[id].locations[index]})});
fs.writeFileSync(path.join(base,'frontend-coverage.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result.summary));
