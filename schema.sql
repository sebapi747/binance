/*create table quotes (
symbol text, price numeric,dt datetime,
primary key(symbol, dt)
);

create table futures (
symbol text, ps text, price numeric,time numeric,
primary key(symbol, time)
);*/

create table cmefut (
code text,
expirationMonth text ,
last numeric,
volume numeric,
updated datetime,
expiry datetime,
primary key(code, updated)
)
