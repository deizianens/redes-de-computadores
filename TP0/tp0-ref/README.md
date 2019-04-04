######
### Existem duas versões compiladas dos programas:

cliente32 e servidor32 foram compilados em uma máquina com CPU de 32 bits
cliente e servidor foram compilados para uma máquina com arquitetura 64 bits

######
As duas versões funcionam com a mesma interface de execução:

## Interface de execução de programas:

### Cliente (modo comum)
`
./cliente [endereco] [porta]
`

### Cliente (modo verbose)
`
./cliente [endereco] [porta] -v
`


### Servidor (modo comum)

`
./servidor [porta]
`

### Servidor (modo verbose)
`
./servidor [porta] -v
`

