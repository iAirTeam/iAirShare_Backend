    Client -1(authContent)--------->UserManager------|
       ^                      |    ^                 |
       |------2(cookie)-------|    |4(checkUserAuth) |5(checkstatus)
       |                           |                 |
       |----3(requireSomething)---->StorageSystem  <-|
       |--------------------------------|
                6(Something)d
