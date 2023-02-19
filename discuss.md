## RCP(Will maybe never implement)

- Request Checkout Process

Client -1(authContent)--------->UserManager------|
^ | ^ |
|------2(cookie)-------| |4(checkUserAuth) |5(checkstatus)
| | |
|----3(requireSomething)---->StorageSystem  <-|
|--------------------------------|
6(Something)d

## Databse V1

## Table Repo

Id, DatabaseName, StructureMapping
0, public, {xddd, xddd, xddd}

## Database V2

### Table File

Id, Name, Pointer, FileSize, #Tag, Property
0, F1, FileId, 2333, 233, {UploadTime: 233333, video: {height:1920, width:1080, fps:30, ...}}
1, F2, FileId, 2333, 3222, {UploadTime: 233333, picture: {width:800, height:900}}

### Table Directory

Id, DName, Pointer, AccessToken
0, D1,     [(Table File>2), (Table File>0), (Table Directory>2)], 123321
1, D2      [(Id)2]
2, D3,     [(Table Directory>0)]

### Table Display

Id, List
0,      (Table Directory>2)