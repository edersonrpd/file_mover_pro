# File Mover Pro

Este projeto fornece uma ferramenta com interface gráfica (GUI) para mover, copiar ou excluir arquivos de um diretório de origem (incluindo todos os subdiretórios) para um diretório de destino.

## Recursos

- Busca recursivamente em todos os subdiretórios do diretório de origem
- Suporta múltiplos tipos de arquivos:
  - Planilhas: `.xlsx`, `.xls`, `.csv`, `.ods`, `.tsv`, `.xlsm`, `.xlsb`, `.xltx`, `.xltm`, `.xlt`, `.xlam`, `.xla`
  - Documentos: `.pdf`, `.doc`, `.docx`, `.txt`, `.rtf`, `.odt`, '.md`
  - Imagens: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.svg`, `.webp`
  - Vídeos: `.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.flv`, `.webm`
  - Áudios: `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.wma`, `.m4a`
  - Arquivos compactados: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`
  - Scripts: `.py`, `.js`, `.sh`, `.bat`, `.pl`, `.rb`
  - SQL: `.sql`
  - Executáveis: `.exe`, `.msi`, `.app`, `.bat`
- Cria automaticamente o diretório de destino se ele não existir
- Trata conflitos de nome
- **Novo:** Suporte a operações de mover, copiar e excluir arquivos
- **Novo:** Pré-visualização mostrando quais arquivos serão afetados com informações de tamanho
- **Novo:** Interface com tema claro/escuro
- **Novo:** Funcionalidade de desfazer para operações de mover

## Instalação

1. Certifique-se de ter o Python instalado
2. Instale as dependências necessárias:
   ```
   pip install PyQt5
   ```

## Uso

1. Execute o aplicativo:
   ```
   python start.py
   ```
   ou
   ```
   python app.py
   ```

2. Selecione o diretório de origem
3. Selecione o diretório de destino (não necessário para operações de exclusão)
4. Escolha os tipos de arquivos a serem processados
5. Selecione a operação desejada (Mover, Copiar ou Excluir)
6. Opcionalmente, clique em "Pré-visualizar" para ver quais arquivos serão afetados
7. Clique em "Executar Operação" para realizar a ação selecionada
8. Para operações de mover, use o botão "Desfazer" para reverter a operação

## Funcionalidades

### Operações
- **Mover:** Move os arquivos do diretório de origem para o diretório de destino
- **Copiar:** Copia os arquivos do diretório de origem para o diretório de destino
- **Excluir:** Exclui os arquivos do diretório de origem (sem necessidade de diretório de destino)

### Pré-visualização
- Mostra uma lista dos arquivos que serão afetados pela operação
- Exibe o tamanho de cada arquivo
- Mostra o caminho de origem e destino para cada arquivo
- Permite confirmar ou cancelar a operação antes de executá-la

### Tema
- Alternância entre tema claro e escuro
- Interface moderna e intuitiva

### Desfazer
- Funcionalidade disponível apenas para operações de mover
- Move os arquivos de volta para seus locais originais
- Requer confirmação antes de executar
- Botão "Desfazer" é habilitado automaticamente após uma operação de mover bem-sucedida

## Requisitos

- Python 3.6+
- PyQt5

## Licença

Veja o arquivo LICENSE para detalhes.