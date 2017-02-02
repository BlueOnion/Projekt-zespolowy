drop table if exists users;
create table users(
    email           text        primary key,
    password_hash   text        not null
);

drop table if exists primers;
create table primers(
    /* INFORMACJA NA TEMAT PRIMERA 1 */
    pid             integer     primary key autoincrement,  /* id primera */
    pname           text        not null,                   /* nazwa primera */
    ptype           text        not null,                   /* typ: forward/reverse */
    psequence       text        not null,                   /* sekwencja (5'->3') */
    nt              integer     not null,                   /* nt */
    temp_gen        real,                                   /* temperatura [C] (wg firmy Genomed) */
    temp_calc       real        not null,                   /* temperatura [C] (kalkulacja) */
    /* INFORMACJE NA TEMAT PRIMERA 2 */
    oligo_date      text,                                   /* data zawieszenia gotowych oligo */
    buffer          text,                                   /* bufor do zawieszenia */
    prep_date       text,                                   /* data przygotowania roztworu wyjściowego */
    /* OPIS SEKWENCJI DOCELOWEJ */
    gene_name       text,                                   /* nazwa genu */
    gb_acc_no       text,                                   /* GenBank ACC No */
    ncbi_id         text,                                   /* NCBI Gene ID */
    ncbi_pa         text,                                   /* NCBI protein acession */
    gene_comment    text,                                   /* dodatkowe uwagi */
    genus           text,                                   /* rodzaj (genus) */
    species         text,                                   /* species */
    gene_desc       text,                                   /* dodatkowy opis np. numer szczepu, serotyp */
    plasmid_name    text,                                   /* nazwa plazmidu */
    seq_desc        text,                                   /* sekwencja docelowa (opis) */
    seq_list        text,                                   /* sekwencja docelowa (losta do wyboru: bakterie, ...) */
    /* WARUNKI AMPLIFIKACJI */
    matrix_prep     text,                                   /* protokół przygotowania matrycy (tekst opisowy) */
    cycles          integer,                                /* liczba cykli */
    final_conc      real,                                   /* stężenie końcowe */
    info            text,                                   /* informacje dodatkowe */
    /* ODNOŚNIKI */
    pmid            text,                                   /* (reference) PMID, numer publikacji */
    /* INFORMACJE NA TEMAT ZAMÓWIENIA */
    order_date      text,                                   /* data zamówienia */
    firm            text,                                   /* firma */
    facture_no      text,                                   /* numer faktury V */
    /* INNE */
    keywords        text,                                   /* słowa kluczowe */
    'status'        integer,                                /* status: dostępny/niedostępny (0/1) */
    'owner'         text        not null                    /* właściciel (email) */
);
 
drop table if exists favourites;
create table favourites(
    pid		    integer	not null,
    email           text	not null
);

