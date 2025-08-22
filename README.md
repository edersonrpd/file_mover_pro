# File Mover Pro

Este projeto fornece uma ferramenta com interface gráfica (GUI) para mover arquivos de um diretório de origem (incluindo todos os subdiretórios) para um diretório de destino.

## Recursos

- Busca recursivamente em todos os subdiretórios do diretório de origem
- Suporta múltiplos tipos de arquivos:
  - Planilhas: `.xlsx`, `.xls`, `.csv`, `.ods`, `.tsv`, `.xlsm`, `.xlsb`, `.xltx`, `.xltm`, `.xlt`, `.xlam`, `.xla`
  - Documentos: `.pdf`, `.doc`, `.docx`, `.txt`, `.rtf`, `.odt`, `.md`
  - Imagens: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.svg`, `.webp`
  - Vídeos: `.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.flv`, `.webm`
  - Áudios: `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.wma`, `.m4a`
  - Arquivos compactados: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`
  - Scripts: `.py`, `.js`, `.sh`, `.bat`, `.pl`, `.rb`
  - SQL: `.sql`
  - Executáveis: `.exe`, `.msi`, `.app`, `.bat`
- Cria automaticamente o diretório de destino se ele não existir
- Trata conflitos de nomes de arquivos adicionando um contador aos nomes duplicados
- Fornece saída detalhada dos arquivos movidos
- Mostra a contagem total de arquivos movidos ao final
- Tema claro/escuro alternável na interface gráfica

## Instalação

Para a versão GUI, instale as dependências necessárias:

```bash
pip install -r requirements.txt
```

## Uso

### Versão GUI

```bash
python app.py
```

Na interface gráfica:
1. Use os botões "Procurar" para selecionar os diretórios de origem e destino
2. Selecione os tipos de arquivos que deseja mover usando as caixas de seleção
3. Clique em "Mover Arquivos Selecionados" para iniciar a operação

## Arquivos neste Projeto

- `app.py`: Versão GUI usando PyQt5 com suporte a tema escuro
- `requirements.txt`: Dependências para a versão GUI
- `README.md`: Este arquivo

## Testes

A aplicação foi testada com vários tipos de arquivos e estruturas de diretórios para garantir seu correto funcionamento.
