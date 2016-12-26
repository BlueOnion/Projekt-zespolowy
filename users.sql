drop table if exists users;
create table users(
    email           text        primary key,
    password_hash   text        not null
);
