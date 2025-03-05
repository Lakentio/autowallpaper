# AutoWallpaper

AutoWallpaper é um script Python que altera automaticamente os wallpapers do seu ambiente de desktop (DE) com base no horário do dia (manhã, tarde e noite). Ele é compatível com diversos ambientes de desktop como XFCE, KDE, GNOME, MATE

## Recursos
- Alterna automaticamente os wallpapers de acordo com o período do dia.
- Configuração via terminal.
- Salva as preferências do usuário.
- Compatível com múltiplos ambientes de desktop.
- Pode ser iniciado automaticamente na inicialização do sistema.

## Requisitos
- Python 3.13 ou superior
- `setuptools` e `pip` instalados
- Um ambiente de desktop compatível (XFCE, KDE, GNOME, MATE, Budgie, etc.)

## Instalação
1. Clone o repositório:
   ```bash
   git clone https://github.com/Lakentio/autowallpaper.git
   cd autowallpaper
   ```

2. Instale o script globalmente:
   ```bash
   sudo python3.13 -m pip install .
   ```

3. Verifique se a instalação foi bem-sucedida:
   ```bash
   autowallpaper --help
   ```

## Configuração
```bash
autowallpaper --manha /caminho/para/wallpaper_manha.jpg autowallpaper --tarde /caminho/para/wallpaper_tarde.jpg autowallpaper --noite /caminho/para/wallpaper_noite.jpg --intervalo 10
```

## Remoção
Para remover o AutoWallpaper do seu sistema:
```bash
sudo python3.13 -m pip uninstall autowallpaper
```

## Contribuição
Qualquer um pode pegar o código e melhorar, afinal até eu não achei que ele ficou bem estruturado.
