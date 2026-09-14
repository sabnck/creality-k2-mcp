# Creality K2 MCP

Dá a clientes MCP contexto local e útil sobre uma Creality K2. O servidor lê o
estado Moonraker, imagens da câmara, perfis locais do slicer, metadados de
G-code e definições de projetos 3MF da Creality. Assim, o cliente consegue
ajudar numa impressão com dados reais em vez de adivinhar.

![Como o Creality K2 MCP liga a impressora aos clientes MCP](assets/k2-mcp-flow.svg)

O alvo testado é a Creality K2 com Moonraker na rede local. O projeto não diz
que outras impressoras são compatíveis sem teste. O guia de adaptadores mostra
como testar e adicionar outra máquina Moonraker sem inventar compatibilidade.

## O que um cliente MCP consegue ver

- Estado atual da impressão, progresso, tempo decorrido e estimativa restante.
- Camadas da K2 por `virtual_sdcard`, mais os ventiladores de modelo e lateral
  pelos pinos específicos `fan0` e `fan2`.
- Temperaturas do bico e da mesa, imagem da câmara, histórico e mensagens
  recentes do Klipper.
- Leitura local de G-code e de projetos 3MF da Creality, sem alterar os
  ficheiros.
- Os perfis que realmente existem no computador.
- Um plano local e revísavel de fatiamento para o Creality Print, sem executar.
- Comandos limitados para a impressora, apenas depois de autorização explícita.
  Não existe envio nem ferramenta para executar G-code arbitrário.

## Começa aqui se não fores dev

Só precisas do modelo da impressora e do endereço local dela. Instala o projeto
do repositório e cola isto no Claude, Codex ou outro cliente MCP que te possa
ajudar a fazer a configuração:

```text
Quero ligar a minha impressora 3D a este projeto Creality K2 MCP.

Modelo da impressora: Creality K2
Endereço local da impressora: YOUR_PRINTER_HOST
Porta da impressora: 7125
Sistema operativo: Windows
Cliente MCP: Claude Desktop ou Codex

Guia-me passo a passo. Mantém o controlo da impressora apenas em leitura no
início. Explica para que serve cada definição, cria a configuração certa para o
cliente local, pede para eu reiniciar o cliente e testa só o estado da
impressora. Não atives nenhum comando que altere a impressora, a não ser que eu
peça isso explicitamente depois de o teste de leitura funcionar.
```

`YOUR_PRINTER_HOST` é só um exemplo. Troca pelo endereço que a tua impressora
tem na tua rede local.

## Instalação manual

Precisas de Python 3.10 ou mais recente, dos ficheiros do projeto e de acesso
local à K2. O Creality Print só é necessário para o planeamento de fatiamento
guiado por perfis.

```powershell
git clone https://github.com/sabnck/creality-k2-mcp.git
cd creality-k2-mcp
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

Depois usa um dos exemplos de configuração:

- [Exemplo para Claude Desktop](examples/claude_desktop_config.json)
- [Exemplo para Codex](examples/codex_config.toml)

Define `K2_HOST` com o endereço local da tua impressora. Deixa
`K2_ALLOW_WRITE` em `0` na primeira ligação. Reinicia o cliente MCP e pergunta:
“Qual é o estado atual da impressora?”

## Primeiro, só leitura

Na configuração normal o projeto apenas lê informação. Podes perguntar:

- “Em que percentagem está a impressão e quanto tempo falta?”
- “Mostra uma imagem atual da câmara e diz se vês algo fora do normal.”
- “Lê este 3MF e explica altura de camada, paredes, infill, suportes e perfil.”
- “Compara estes dois G-code pelo tempo previsto, peso de filamento e camadas.”
- “Que perfis K2 para bico 0.4 existem mesmo neste computador?”

## Controlo opcional da impressora

Só define `K2_ALLOW_WRITE=1` se quiseres que o cliente consiga alterar uma
impressora real. Mesmo assim, cada ação tem limites:

| Ação | Proteção |
| --- | --- |
| Pausar ou retomar | Exige escrita ativada. |
| Cancelar | Exige `confirm='CONFIRM'`. |
| Temperatura do bico | 0 até `K2_MAX_NOZZLE`, teto padrão de 280 C. |
| Temperatura da mesa | 0 até `K2_MAX_BED`, teto padrão de 110 C. |
| Velocidade | 30 a 150 por cento. |
| Ventilador do modelo | 0 a 100 por cento. |

Não há, de propósito, envio ou ferramenta genérica para executar G-code.

## Compatibilidade

| Equipamento | Estado | Nota |
| --- | --- | --- |
| Creality K2 com Moonraker local | Verificado | É o alvo deste projeto. |
| Outra impressora Creality | Não verificado | Usa o guia de adaptadores e testa os objetos reais. |
| Impressora Moonraker ou Klipper genérica | Não verificado | O transporte pode ser parecido, mas os objetos e limites podem mudar. |

## Problemas comuns

| Sintoma | O que verificar |
| --- | --- |
| Não liga ao estado | Confirma que a impressora está ligada, acessível na rede local, e que `K2_HOST` e `K2_PORT` estão certos. |
| Camadas desconhecidas | Confirma se a impressora expõe `virtual_sdcard`; é a fonte usada pela K2. |
| Câmara indisponível | Verifica `K2_CAM_PORT` e abre a câmara da K2 no browser, na mesma rede. |
| Perfis vazios | Aponta `K2_PROFILES` para `resources/profiles/Creality` do Creality Print. |
| Não encontra o Creality Print | Define `K2_CLI` para o executável local do CrealityPrint. |

Lê [Segurança](docs/SAFETY.md) antes de ativar comandos. Para outra máquina,
lê o [guia de adaptadores](docs/ADAPTER_GUIDE.md).

English: [README.md](README.md)

## Contribuições e licença

Ao reportar compatibilidade, inclui o modelo, contexto de firmware, resposta de
objetos sanitizada e o que testaste de verdade. Não incluas endereços locais,
capturas, G-code, modelos ou credenciais.

Criado e mantido por Fernandes. Licenciado sob a [MIT License](LICENSE).
