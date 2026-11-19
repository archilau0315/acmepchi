@echo off
chcp 65001 >nul
set "PYTHONPATH=%~dp0..\src"
start "" pythonw -m acme_lp.gui
