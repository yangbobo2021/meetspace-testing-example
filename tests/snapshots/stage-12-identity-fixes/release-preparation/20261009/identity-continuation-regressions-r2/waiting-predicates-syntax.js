// Test-only predicates; syntax check only, never execute.
const preparedPredicates = [
(() => state.user && !state.loading && !state.loadError && !state.identityPending && !!document.querySelector("#filter-date")),
(() => state.user?.role==="member" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("#filter-date") && !document.querySelector("nav [data-page=manage]")),
(() => state.user && !state.loading && !state.identityPending && !state.loadError && document.querySelector("#toast").textContent==="成员角色已更新"),
(() => state.user?.role==="member" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("#filter-date") && !document.querySelector("nav [data-page=manage]")),
(() => document.querySelector("#toast").textContent.length>0),
(() => state.user?.role==="member" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("#filter-date")),
(() => document.querySelector("#toast").textContent.length>0 && document.querySelector("#toast").textContent!=="成员角色已更新"),
(() => state.user?.role==="member" && state.identityPending && state.loadError==="新角色提交后身份查询503"),
(() => state.user?.role==="member" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("#filter-date") && !document.querySelector("nav [data-page=manage]")),
(() => state.user?.role === "admin" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("[data-member]") && document.querySelector("#toast").textContent === "成员角色已更新"),
(() => document.querySelector("#toast").textContent==="通知已标为已读"),
(() => state.user.role==="member" && !state.identityPending && !state.loading && state.page==="spaces" && !document.querySelector("nav [data-page=manage]") && document.querySelector("#toast").textContent==="成员角色已更新"),
(() => document.querySelector("#toast").textContent==="注入他人角色PATCH不可用"),
(() => state.user && !state.loading && !state.loadError),
(() => !state.user || !state.loading),
(() => state.user && !state.loading && !state.identityPending && !state.loadError),
(() => !state.loading),
(() => state.user?.role === "member" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("#filter-date") && !document.querySelector("nav [data-page=manage]") && document.querySelector("#toast").textContent==="成员角色已更新"),
(() => !state.loading)
];
