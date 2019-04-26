# DCCNET testing infrastructure

Este pacote apresenta uma implementação do DCCNET e casos de teste
que você pode utilizar durante a avaliação do DCCNET.  O seu
programa deverá interoperar com outros, incluindo o fornecido neste
pacote.  Por isso, é recomendado que você o utilize em alguma etapa dos seus 
testes.

O programa `dccnet` foi compilado para uma máquina com arquitetura 64 bits, 
enquanto o programa `dccnet32` foi compilado para uma máquina com 
arquitetura 32 bits.

O programa fornecido apresenta algumas mensagens na saída padrão.
Elas podem ser úteis durante os testes.  Execute algum exemplo onde
tanto o servidor quanto o cliente são o `dccnet` fornecido. Assim,
você se familiariza com as mensagens.

## Casos de teste

O diretório `tests` contém cinco casos de testes que você pode utilizar
para testar seu programa.  Os arquivos sem sufixo são os arquivos
originais, que podem ser utilizados como entrada do programa.  Ou
seja, dados a serem transmitidos por um programa e,
consequentemente, recebidos pelo outro programa.
