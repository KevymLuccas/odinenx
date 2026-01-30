# -*- coding: utf-8 -*-
"""
🏆 CARTOLA FC MANAGER PRO 2.0 🏆
Sistema Inteligente de Escalação - Brasileirão
Desenvolvido com PyQt5 + APIs Múltiplas + IA Avançada
"""

import sys
import json
import requests
import random
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QComboBox,
    QSpinBox, QDoubleSpinBox, QGroupBox, QTabWidget, QProgressBar,
    QMessageBox, QHeaderView, QFrame, QSplitter, QTextEdit,
    QGridLayout, QScrollArea, QCheckBox, QLineEdit, QSlider
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QLinearGradient, QBrush

# ====================== CONFIGURAÇÕES DAS APIs ======================
API_BASE = "https://api.cartola.globo.com"

ENDPOINTS = {
    "mercado": f"{API_BASE}/atletas/mercado",
    "clubes": f"{API_BASE}/clubes",
    "status": f"{API_BASE}/mercado/status",
    "partidas": f"{API_BASE}/partidas",
    "pontuados": f"{API_BASE}/atletas/pontuados",
    "rodadas": f"{API_BASE}/rodadas",
    "partidas_rodada": f"{API_BASE}/partidas/{{rodada}}",
}

# ====================== STATUS DOS ATLETAS ======================
STATUS_ATLETA = {
    2: {"nome": "Dúvida", "emoji": "⚠️", "cor": "#ffaa00"},
    3: {"nome": "Suspenso", "emoji": "🟡", "cor": "#ffff00"},
    5: {"nome": "Contundido", "emoji": "🏥", "cor": "#ff6666"},
    6: {"nome": "Nulo", "emoji": "❓", "cor": "#888888"},
    7: {"nome": "Provável", "emoji": "✅", "cor": "#00ff88"},
}

# ====================== DADOS HISTÓRICOS DOS TIMES (Brasileirão) ======================
# Força ofensiva e defensiva baseada em temporadas anteriores
FORCA_TIMES = {
    # time_id: {ataque, defesa, casa, fora} (escala 0-100)
    262: {"nome": "Flamengo", "ataque": 88, "defesa": 75, "casa": 85, "fora": 78},
    263: {"nome": "Botafogo", "ataque": 82, "defesa": 78, "casa": 80, "fora": 75},
    264: {"nome": "Fluminense", "ataque": 72, "defesa": 70, "casa": 75, "fora": 65},
    266: {"nome": "Fluminense", "ataque": 70, "defesa": 68, "casa": 72, "fora": 62},
    275: {"nome": "Palmeiras", "ataque": 90, "defesa": 85, "casa": 92, "fora": 82},
    276: {"nome": "São Paulo", "ataque": 78, "defesa": 80, "casa": 82, "fora": 72},
    277: {"nome": "Santos", "ataque": 70, "defesa": 65, "casa": 75, "fora": 60},
    282: {"nome": "Atlético-MG", "ataque": 80, "defesa": 72, "casa": 85, "fora": 70},
    283: {"nome": "Cruzeiro", "ataque": 75, "defesa": 70, "casa": 78, "fora": 68},
    284: {"nome": "Grêmio", "ataque": 76, "defesa": 74, "casa": 82, "fora": 68},
    285: {"nome": "Internacional", "ataque": 78, "defesa": 76, "casa": 84, "fora": 70},
    286: {"nome": "Vasco", "ataque": 68, "defesa": 65, "casa": 72, "fora": 58},
    287: {"nome": "Bahia", "ataque": 74, "defesa": 68, "casa": 80, "fora": 62},
    288: {"nome": "Vitória", "ataque": 62, "defesa": 58, "casa": 70, "fora": 52},
    290: {"nome": "Corinthians", "ataque": 75, "defesa": 70, "casa": 80, "fora": 65},
    292: {"nome": "Sport", "ataque": 60, "defesa": 55, "casa": 68, "fora": 50},
    293: {"nome": "Fortaleza", "ataque": 76, "defesa": 78, "casa": 85, "fora": 68},
    294: {"nome": "Ceará", "ataque": 64, "defesa": 62, "casa": 72, "fora": 55},
    315: {"nome": "RB Bragantino", "ataque": 72, "defesa": 70, "casa": 76, "fora": 66},
    354: {"nome": "Juventude", "ataque": 58, "defesa": 60, "casa": 68, "fora": 50},
    356: {"nome": "Athletico-PR", "ataque": 74, "defesa": 72, "casa": 80, "fora": 65},
    373: {"nome": "Cuiabá", "ataque": 55, "defesa": 58, "casa": 65, "fora": 48},
    2305: {"nome": "Mirassol", "ataque": 58, "defesa": 55, "casa": 68, "fora": 48},
}

# Pontuação média por posição (histórico Cartola)
MEDIA_POSICAO = {
    1: 3.5,   # Goleiro
    2: 3.8,   # Lateral
    3: 3.2,   # Zagueiro
    4: 4.5,   # Meia
    5: 5.2,   # Atacante
    6: 2.8,   # Técnico
}

POSICOES = {
    1: "Goleiro",
    2: "Lateral",
    3: "Zagueiro", 
    4: "Meia",
    5: "Atacante",
    6: "Técnico"
}

POSICOES_ABREV = {
    1: "GOL",
    2: "LAT",
    3: "ZAG",
    4: "MEI",
    5: "ATA",
    6: "TEC"
}

# Scouts e seus valores de pontuação no Cartola
SCOUTS_PONTUACAO = {
    # Positivos
    "G": 8.0,     # Gol
    "A": 5.0,     # Assistência
    "FT": 3.5,    # Finalização na trave
    "FD": 1.2,    # Finalização defendida
    "FF": 0.8,    # Finalização pra fora
    "FS": 0.5,    # Falta sofrida
    "PS": 1.0,    # Penalti sofrido
    "DS": 1.2,    # Desarme
    "SG": 5.0,    # Jogo sem sofrer gol
    "DE": 3.0,    # Defesa goleiro
    "DP": 7.0,    # Defesa de penalti
    "GC": -5.0,   # Gol contra
    "CV": -5.0,   # Cartão vermelho
    "CA": -2.0,   # Cartão amarelo
    "GS": -2.0,   # Gol sofrido
    "PP": -4.0,   # Penalti perdido
    "FC": -0.5,   # Falta cometida
    "I": -0.5,    # Impedimento
    "PI": -0.5,   # Passe incompleto (técnico)
}

# Esquema tático FIXO: 1 GOL, 2 LAT, 2 ZAG, 4 MEI, 2 ATA, 1 TEC
# Layout: GOL | LAT-ZAG-ZAG-LAT | MEI-MEI-MEI-MEI | ATA-ATA | TEC
ESQUEMA_PADRAO = {
    1: 1,  # Goleiro
    2: 2,  # Laterais
    3: 2,  # Zagueiros
    4: 4,  # Meias (4!)
    5: 2,  # Atacantes
    6: 1   # Técnico
}

# Reservas fixas: GOL, LAT, ZAG, MEI, ATA
RESERVAS_POSICOES = [1, 2, 3, 4, 5]  # GOL, LAT, ZAG, MEI, ATA

# URL base para fotos de atletas
FOTO_URL_BASE = "https://s.sde.globo.com/media/pessoa_cartolafc/foto/{atleta_id}/100x100"

# Todos os esquemas disponíveis no Cartola (mantemos mas usamos o fixo)
ESQUEMAS_TATICOS = {
    "4-4-2 🎯": {1: 1, 2: 2, 3: 2, 4: 4, 5: 2, 6: 1},  # NOSSO PADRÃO
    "3-4-3": {1: 1, 2: 1, 3: 3, 4: 3, 5: 3, 6: 1},
    "3-5-2": {1: 1, 2: 1, 3: 3, 4: 4, 5: 2, 6: 1},
    "4-3-3": {1: 1, 2: 2, 3: 2, 4: 2, 5: 4, 6: 1},
    "4-5-1": {1: 1, 2: 2, 3: 2, 4: 4, 5: 2, 6: 1},
    "5-3-2": {1: 1, 2: 2, 3: 3, 4: 2, 5: 3, 6: 1},
    "5-4-1": {1: 1, 2: 2, 3: 3, 4: 3, 5: 2, 6: 1},
}

# ====================== ESTILOS CSS ======================
DARK_STYLE = """
QMainWindow {
    background-color: #0a0a0a;
}
QWidget {
    background-color: #0a0a0a;
    color: #ffffff;
    font-family: 'Segoe UI', Arial;
    font-size: 11px;
}
QGroupBox {
    background-color: #1a1a1a;
    border: 2px solid #9b59b6;
    border-radius: 10px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
    font-size: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 10px;
    color: #bb86fc;
    font-size: 12px;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #9b59b6, stop:1 #8e44ad);
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 11px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #bb86fc, stop:1 #9b59b6);
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #7b2cbf, stop:1 #5a189a);
}
QPushButton#btnEscalar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #9b59b6, stop:0.5 #bb86fc, stop:1 #9b59b6);
    font-size: 14px;
    padding: 10px 25px;
    border-radius: 10px;
    border: 2px solid #bb86fc;
}
QPushButton#btnEscalar:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #bb86fc, stop:0.5 #e0aaff, stop:1 #bb86fc);
    border: 2px solid #e0aaff;
}
QPushButton#btnReserva {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6c5ce7, stop:1 #a29bfe);
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid #a29bfe;
}
QPushButton#btnReserva:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #a29bfe, stop:1 #dfe6e9);
    color: #2d3436;
}
QTableWidget {
    background-color: #1a1a1a;
    alternate-background-color: #0f0f0f;
    border: 1px solid #3d3d3d;
    border-radius: 8px;
    gridline-color: #2d2d2d;
    selection-background-color: #9b59b6;
}
QTableWidget::item {
    padding: 4px;
    border-bottom: 1px solid #2d2d2d;
    color: #ffffff;
}
QTableWidget::item:selected {
    background-color: #9b59b6;
    color: #ffffff;
}
QTableWidget::item:hover {
    background-color: #2d2d2d;
}
QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #2d2d2d, stop:1 #1a1a1a);
    color: #bb86fc;
    padding: 6px;
    border: none;
    border-bottom: 2px solid #9b59b6;
    font-weight: bold;
    font-size: 11px;
}
QComboBox {
    background-color: #1a1a1a;
    border: 1px solid #9b59b6;
    border-radius: 6px;
    padding: 4px 8px;
    min-width: 80px;
    color: #ffffff;
    font-size: 11px;
}
QComboBox:hover {
    border-color: #bb86fc;
    background-color: #2d2d2d;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
    background: transparent;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #bb86fc;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #1a1a1a;
    border: 1px solid #9b59b6;
    border-radius: 6px;
    selection-background-color: #9b59b6;
    color: #ffffff;
}
QSpinBox, QDoubleSpinBox {
    background-color: #1a1a1a;
    border: 1px solid #9b59b6;
    border-radius: 6px;
    padding: 4px;
    color: #ffffff;
    font-size: 11px;
}
QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #bb86fc;
    background-color: #2d2d2d;
}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #9b59b6;
    border-radius: 3px;
    width: 16px;
}
QLineEdit {
    background-color: #1a1a1a;
    border: 1px solid #9b59b6;
    border-radius: 6px;
    padding: 4px 8px;
    color: #ffffff;
    selection-background-color: #9b59b6;
    font-size: 11px;
}
QLineEdit:focus {
    border-color: #bb86fc;
    background-color: #2d2d2d;
}
QProgressBar {
    background-color: #1a1a1a;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    height: 18px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
    font-size: 10px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #9b59b6, stop:0.5 #bb86fc, stop:1 #9b59b6);
    border-radius: 5px;
}
QTabWidget::pane {
    border: 2px solid #9b59b6;
    border-radius: 10px;
    background-color: #1a1a1a;
    top: -2px;
}
QTabBar::tab {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #2d2d2d, stop:1 #1a1a1a);
    color: #ffffff;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border: 1px solid #3d3d3d;
    border-bottom: none;
    font-weight: bold;
    font-size: 11px;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #9b59b6, stop:1 #8e44ad);
    border-color: #9b59b6;
    color: #ffffff;
}
QTabBar::tab:hover:!selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #3d3d3d, stop:1 #2d2d2d);
    border-color: #bb86fc;
}
QScrollBar:vertical {
    background-color: #1a1a1a;
    width: 10px;
    border-radius: 5px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #9b59b6, stop:1 #bb86fc);
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #bb86fc, stop:1 #e0aaff);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #1a1a1a;
    height: 10px;
    border-radius: 5px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #9b59b6, stop:1 #bb86fc);
    border-radius: 5px;
    min-width: 30px;
}
QTextEdit {
    background-color: #1a1a1a;
    border: 1px solid #9b59b6;
    border-radius: 8px;
    padding: 6px;
    color: #ffffff;
    selection-background-color: #9b59b6;
    font-size: 11px;
}
QLabel#titulo {
    font-size: 22px;
    font-weight: bold;
    color: #bb86fc;
}
QLabel#subtitulo {
    font-size: 11px;
    color: #a0a0a0;
}
QLabel#status {
    font-size: 11px;
    color: #bb86fc;
    padding: 4px;
}
QLabel#valorTotal {
    font-size: 16px;
    font-weight: bold;
    color: #00ff88;
}
QLabel#valorReserva {
    font-size: 14px;
    font-weight: bold;
    color: #a29bfe;
}
QCheckBox {
    spacing: 6px;
    color: #ffffff;
    font-size: 11px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #9b59b6;
    background-color: #1a1a1a;
}
QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #9b59b6, stop:1 #bb86fc);
    border-color: #bb86fc;
}
QCheckBox::indicator:hover {
    border-color: #bb86fc;
}
QSlider::groove:horizontal {
    background: #2d2d2d;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #9b59b6, stop:1 #bb86fc);
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
    border: 1px solid #bb86fc;
}
QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #bb86fc, stop:1 #e0aaff);
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #9b59b6, stop:1 #bb86fc);
    border-radius: 3px;
}
QFrame#cardFrame {
    background-color: #1a1a1a;
    border: 1px solid #9b59b6;
    border-radius: 10px;
    padding: 8px;
}
QFrame#reservaFrame {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1a1a1a, stop:1 #2d1f3d);
    border: 1px solid #a29bfe;
    border-radius: 10px;
    padding: 6px;
}
"""


# ====================== THREAD PARA CARREGAR DADOS ======================
class CarregadorDados(QThread):
    """Thread para carregar dados da API sem travar a interface"""
    progresso = pyqtSignal(int)
    finalizado = pyqtSignal(dict)
    erro = pyqtSignal(str)
    
    def run(self):
        try:
            dados = {}
            
            # Carregar status do mercado
            self.progresso.emit(5)
            response = requests.get(ENDPOINTS["status"], timeout=15)
            if response.status_code == 200:
                dados["status"] = response.json()
            
            # Carregar clubes
            self.progresso.emit(15)
            response = requests.get(ENDPOINTS["clubes"], timeout=15)
            if response.status_code == 200:
                dados["clubes"] = response.json()
            
            # Carregar atletas do mercado
            self.progresso.emit(30)
            response = requests.get(ENDPOINTS["mercado"], timeout=30)
            if response.status_code == 200:
                dados["mercado"] = response.json()
            
            # Carregar partidas da rodada atual
            self.progresso.emit(50)
            response = requests.get(ENDPOINTS["partidas"], timeout=15)
            if response.status_code == 200:
                dados["partidas"] = response.json()
            
            # Carregar todas as rodadas
            self.progresso.emit(65)
            response = requests.get(ENDPOINTS["rodadas"], timeout=15)
            if response.status_code == 200:
                dados["rodadas"] = response.json()
            
            # Carregar dados detalhados da rodada atual
            self.progresso.emit(75)
            rodada_atual = dados.get("status", {}).get("rodada_atual", 1)
            url_rodada = ENDPOINTS["partidas_rodada"].format(rodada=rodada_atual)
            response = requests.get(url_rodada, timeout=15)
            if response.status_code == 200:
                dados["partidas_detalhadas"] = response.json()
            
            # Tentar carregar pontuados (pode não estar disponível)
            self.progresso.emit(85)
            try:
                response = requests.get(ENDPOINTS["pontuados"], timeout=15)
                if response.status_code == 200:
                    dados["pontuados"] = response.json()
            except:
                pass
            
            self.progresso.emit(100)
            self.finalizado.emit(dados)
            
        except requests.exceptions.RequestException as e:
            self.erro.emit(f"Erro de conexão: {str(e)}")
        except Exception as e:
            self.erro.emit(f"Erro: {str(e)}")


# ====================== ALGORITMO DE ESCALAÇÃO AVANÇADO ======================
class AnalisadorConfronto:
    """Analisa confrontos e calcula probabilidades"""
    
    @staticmethod
    def get_forca_time(clube_id):
        """Retorna força do time ou valores padrão"""
        return FORCA_TIMES.get(clube_id, {
            "nome": "Desconhecido",
            "ataque": 65,
            "defesa": 65,
            "casa": 70,
            "fora": 60
        })
    
    @staticmethod
    def calcular_fator_confronto(clube_id, adversario_id, mandante=True):
        """
        Calcula fator de bonificação baseado no confronto
        Retorna valor entre 0.7 e 1.5
        """
        time = AnalisadorConfronto.get_forca_time(clube_id)
        adversario = AnalisadorConfronto.get_forca_time(adversario_id)
        
        # Força ofensiva vs defesa adversária
        if mandante:
            forca_ataque = time["ataque"] * (time["casa"] / 100)
            fraqueza_defesa = 100 - adversario["defesa"] * (adversario["fora"] / 100)
        else:
            forca_ataque = time["ataque"] * (time["fora"] / 100)
            fraqueza_defesa = 100 - adversario["defesa"] * (adversario["casa"] / 100)
        
        # Calcular fator (normalizado entre 0.7 e 1.5)
        fator_bruto = (forca_ataque + fraqueza_defesa) / 150
        fator = max(0.7, min(1.5, fator_bruto + 0.5))
        
        return fator
    
    @staticmethod
    def calcular_potencial_gols(clube_id, adversario_id, mandante=True):
        """Estima potencial de gols do time"""
        time = AnalisadorConfronto.get_forca_time(clube_id)
        adversario = AnalisadorConfronto.get_forca_time(adversario_id)
        
        ataque = time["ataque"] * (1.1 if mandante else 0.9)
        defesa_adv = adversario["defesa"] * (0.9 if mandante else 1.1)
        
        # Potencial de gols (0-5 escala)
        potencial = ((ataque - defesa_adv) / 30) + 1.5
        return max(0.5, min(4.0, potencial))
    
    @staticmethod
    def calcular_potencial_saldo(clube_id, adversario_id, mandante=True):
        """Estima potencial de saldo de gols (para SG)"""
        time = AnalisadorConfronto.get_forca_time(clube_id)
        adversario = AnalisadorConfronto.get_forca_time(adversario_id)
        
        defesa = time["defesa"] * (1.1 if mandante else 0.9)
        ataque_adv = adversario["ataque"] * (0.9 if mandante else 1.1)
        
        # Chance de SG (0-100%)
        chance_sg = ((defesa - ataque_adv) / 2) + 30
        return max(5, min(60, chance_sg))


class EscaladorInteligente:
    """Algoritmo inteligente para montar a melhor escalação"""
    
    def __init__(self, atletas, clubes, partidas=None, cartoletas=100.0):
        self.atletas = atletas
        self.clubes = clubes
        self.partidas = partidas or []
        self.cartoletas = cartoletas
        self.confrontos = self._mapear_confrontos()
    
    def _mapear_confrontos(self):
        """Mapeia confrontos da rodada por clube"""
        confrontos = {}
        for partida in self.partidas:
            casa_id = partida.get("clube_casa_id")
            fora_id = partida.get("clube_visitante_id")
            
            if casa_id and fora_id:
                confrontos[casa_id] = {
                    "adversario": fora_id,
                    "mandante": True,
                    "local": partida.get("local", "")
                }
                confrontos[fora_id] = {
                    "adversario": casa_id,
                    "mandante": False,
                    "local": partida.get("local", "")
                }
        return confrontos
    
    def calcular_score(self, atleta, pesos=None):
        """Calcula score de um atleta baseado em múltiplos fatores avançados"""
        if pesos is None:
            pesos = {
                "media": 0.30,
                "preco": 0.15,
                "variacao": 0.10,
                "jogos": 0.08,
                "confronto": 0.20,
                "potencial_gols": 0.12,
                "consistencia": 0.05
            }
        
        # ===== 1. MÉDIA DE PONTOS (normalizado 0-10) =====
        media = atleta.get("media_num", 0)
        media_norm = min(media / 2, 10)  # Normaliza para escala 0-10
        
        # ===== 2. CUSTO-BENEFÍCIO =====
        preco = max(atleta.get("preco_num", 1), 0.1)
        custo_beneficio = (media / preco) * 5  # Normalizado
        custo_beneficio = min(custo_beneficio, 10)
        
        # ===== 3. VARIAÇÃO (momentum) =====
        variacao = atleta.get("variacao_num", 0)
        # Jogador em alta valorização = boa fase
        var_norm = (variacao + 5) / 10 * 10  # Normaliza -5 a +5 para 0-10
        var_norm = max(0, min(10, var_norm))
        
        # ===== 4. EXPERIÊNCIA (jogos) =====
        jogos = atleta.get("jogos_num", 0)
        jogos_norm = min(jogos / 4, 10)  # 4+ jogos = máximo
        
        # ===== 5. FATOR CONFRONTO (NOVO!) =====
        clube_id = atleta.get("clube_id")
        confronto = self.confrontos.get(clube_id, {})
        
        if confronto:
            adversario_id = confronto.get("adversario")
            mandante = confronto.get("mandante", False)
            fator_confronto = AnalisadorConfronto.calcular_fator_confronto(
                clube_id, adversario_id, mandante
            )
            # Bônus por mandante
            if mandante:
                fator_confronto *= 1.1
        else:
            fator_confronto = 1.0
        
        confronto_norm = (fator_confronto - 0.7) / 0.8 * 10  # Normaliza 0.7-1.5 para 0-10
        confronto_norm = max(0, min(10, confronto_norm))
        
        # ===== 6. POTENCIAL DE GOLS POR POSIÇÃO =====
        posicao_id = atleta.get("posicao_id", 4)
        potencial_gols = 5  # Base
        
        if confronto:
            adversario_id = confronto.get("adversario")
            mandante = confronto.get("mandante", False)
            
            # Atacantes e meias se beneficiam de confronto ofensivo favorável
            if posicao_id in [4, 5]:  # Meia ou Atacante
                pot_gols = AnalisadorConfronto.calcular_potencial_gols(
                    clube_id, adversario_id, mandante
                )
                potencial_gols = pot_gols * 2.5  # Escala para 0-10
            
            # Goleiros e zagueiros se beneficiam de confronto defensivo favorável
            elif posicao_id in [1, 3]:  # Goleiro ou Zagueiro
                chance_sg = AnalisadorConfronto.calcular_potencial_saldo(
                    clube_id, adversario_id, mandante
                )
                potencial_gols = chance_sg / 6  # Escala para 0-10
            
            # Laterais são híbridos
            elif posicao_id == 2:  # Lateral
                pot_gols = AnalisadorConfronto.calcular_potencial_gols(
                    clube_id, adversario_id, mandante
                )
                chance_sg = AnalisadorConfronto.calcular_potencial_saldo(
                    clube_id, adversario_id, mandante
                )
                potencial_gols = (pot_gols * 1.5 + chance_sg / 10) / 2
        
        potencial_gols = max(0, min(10, potencial_gols))
        
        # ===== 7. CONSISTÊNCIA (desvio padrão implícito) =====
        # Quanto mais jogos com boa média = mais consistente
        if jogos > 0 and media > 0:
            consistencia = min((media * jogos) / 20, 10)
        else:
            consistencia = 3  # Sem dados = neutro
        
        # ===== CALCULAR SCORE FINAL =====
        score = (
            media_norm * pesos["media"] +
            custo_beneficio * pesos["preco"] +
            var_norm * pesos["variacao"] +
            jogos_norm * pesos["jogos"] +
            confronto_norm * pesos["confronto"] +
            potencial_gols * pesos["potencial_gols"] +
            consistencia * pesos["consistencia"]
        )
        
        # Penalidades por status
        status = atleta.get("status_id", 0)
        if status == 2:  # Dúvida
            score *= 0.7
        elif status != 7:  # Não é provável
            score *= 0.3
        
        return round(score, 2)
    
    def escalar_time(self, esquema=None, considerar_preco=True, evitar_suspensos=True):
        """Monta a melhor escalação possível usando algoritmo avançado"""
        if esquema is None:
            esquema = ESQUEMA_PADRAO.copy()
        
        # Filtrar atletas válidos
        atletas_validos = []
        for atleta in self.atletas:
            status = atleta.get("status_id", 0)
            if evitar_suspensos and status != 7:
                continue
            atleta["score"] = self.calcular_score(atleta)
            atletas_validos.append(atleta)
        
        # Separar por posição e ordenar por score
        por_posicao = {}
        for pos_id in POSICOES.keys():
            por_posicao[pos_id] = sorted(
                [a for a in atletas_validos if a.get("posicao_id") == pos_id],
                key=lambda x: x["score"],
                reverse=True
            )
        
        # Algoritmo de otimização com backtracking simplificado
        melhor_escalacao = []
        melhor_score = 0
        
        # Tentar 3 estratégias diferentes
        for estrategia in range(3):
            escalacao = []
            gasto_total = 0.0
            
            # Definir ordem de preenchimento baseada na estratégia
            if estrategia == 0:
                # Priorizar posições com mais valor (ATA > MEI > LAT > ZAG > GOL > TEC)
                ordem_posicoes = [5, 4, 2, 3, 1, 6]
            elif estrategia == 1:
                # Priorizar posições mais baratas primeiro
                ordem_posicoes = [6, 1, 3, 2, 4, 5]
            else:
                # Ordem padrão
                ordem_posicoes = list(esquema.keys())
            
            for pos_id in ordem_posicoes:
                quantidade = esquema.get(pos_id, 0)
                candidatos = por_posicao.get(pos_id, [])
                selecionados = 0
                
                # Skip de candidatos baseado na estratégia
                skip = estrategia if estrategia < 2 else 0
                
                for i, atleta in enumerate(candidatos):
                    if selecionados >= quantidade:
                        break
                    
                    # Pular alguns candidatos para diversificar
                    if i < skip and len(candidatos) > quantidade + skip:
                        continue
                    
                    preco = atleta.get("preco_num", 0)
                    
                    if considerar_preco and (gasto_total + preco) > self.cartoletas:
                        continue
                    
                    if atleta["atleta_id"] in [a["atleta_id"] for a in escalacao]:
                        continue
                    
                    escalacao.append(atleta)
                    gasto_total += preco
                    selecionados += 1
            
            # Calcular score total da escalação
            score_total = sum(a["score"] for a in escalacao)
            
            if score_total > melhor_score:
                melhor_score = score_total
                melhor_escalacao = escalacao.copy()
        
        gasto_final = sum(a.get("preco_num", 0) for a in melhor_escalacao)
        return melhor_escalacao, gasto_final
    
    def analisar_confrontos(self, partidas):
        """Analisa os confrontos da rodada com insights"""
        analise = []
        for partida in partidas:
            casa_id = partida.get("clube_casa_id")
            fora_id = partida.get("clube_visitante_id")
            
            casa = self.clubes.get(str(casa_id), {})
            fora = self.clubes.get(str(fora_id), {})
            
            # Calcular expectativas
            pot_gols_casa = AnalisadorConfronto.calcular_potencial_gols(casa_id, fora_id, True)
            pot_gols_fora = AnalisadorConfronto.calcular_potencial_gols(fora_id, casa_id, False)
            chance_sg_casa = AnalisadorConfronto.calcular_potencial_saldo(casa_id, fora_id, True)
            chance_sg_fora = AnalisadorConfronto.calcular_potencial_saldo(fora_id, casa_id, False)
            
            analise.append({
                "mandante": casa.get("nome", "?"),
                "visitante": fora.get("nome", "?"),
                "local": partida.get("local", ""),
                "data": partida.get("partida_data", ""),
                "pot_gols_casa": pot_gols_casa,
                "pot_gols_fora": pot_gols_fora,
                "chance_sg_casa": chance_sg_casa,
                "chance_sg_fora": chance_sg_fora,
            })
        return analise


# ====================== JANELA PRINCIPAL ======================
class CartolaFCManager(QMainWindow):
    """Janela principal do aplicativo"""
    
    def __init__(self):
        super().__init__()
        self.dados = {}
        self.atletas = []
        self.clubes = {}
        self.partidas = []
        self.escalacao_atual = []
        self.reservas_atual = []  # Lista de reservas
        self.capitao_atual = None  # Capitão do time
        self.confrontos_analise = []
        self.confrontos_map = {}  # Mapa de confrontos
        
        self.initUI()
        
    def initUI(self):
        """Inicializa a interface do usuário"""
        self.setWindowTitle("⚽ CARTOLA FC MANAGER PRO 2.0 - Brasileirão 2026 🏆")
        self.setGeometry(50, 50, 1400, 850)
        self.setStyleSheet(DARK_STYLE)
        
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        layout_principal = QVBoxLayout(central)
        layout_principal.setSpacing(8)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        
        # ===== HEADER =====
        header = self.criar_header()
        layout_principal.addWidget(header)
        
        # ===== ABAS PRINCIPAIS =====
        self.tabs = QTabWidget()
        layout_principal.addWidget(self.tabs)
        
        # Tab 1: Dashboard
        tab_dashboard = self.criar_tab_dashboard()
        self.tabs.addTab(tab_dashboard, "🏠 Dashboard")
        
        # Tab 2: Mercado de Atletas
        tab_mercado = self.criar_tab_mercado()
        self.tabs.addTab(tab_mercado, "📊 Mercado")
        
        # Tab 3: Escalação Inteligente
        tab_escalacao = self.criar_tab_escalacao()
        self.tabs.addTab(tab_escalacao, "⚡ Escalação IA")
        
        # Tab 4: VISUAL DO TIME (CAMPO) - NOVA!
        tab_campo = self.criar_tab_campo_visual()
        self.tabs.addTab(tab_campo, "🏟️ Meu Time")
        
        # Tab 5: Confrontos
        tab_confrontos = self.criar_tab_confrontos()
        self.tabs.addTab(tab_confrontos, "⚔️ Confrontos")
        
        # Tab 6: Análises
        tab_analises = self.criar_tab_analises()
        self.tabs.addTab(tab_analises, "📈 Análises")
        
        # ===== BARRA DE STATUS =====
        self.status_bar = QLabel("🔄 Clique em 'Atualizar Dados' para começar")
        self.status_bar.setObjectName("status")
        layout_principal.addWidget(self.status_bar)
        
        # Carregar dados automaticamente
        QTimer.singleShot(500, self.carregar_dados)
    
    def criar_header(self):
        """Cria o cabeçalho do aplicativo"""
        header = QFrame()
        header.setMaximumHeight(60)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Título
        titulo_container = QVBoxLayout()
        titulo_container.setSpacing(0)
        titulo = QLabel("⚽ CARTOLA FC MANAGER PRO")
        titulo.setObjectName("titulo")
        subtitulo = QLabel("Brasileirão 2026")
        subtitulo.setObjectName("subtitulo")
        titulo_container.addWidget(titulo)
        titulo_container.addWidget(subtitulo)
        layout.addLayout(titulo_container)
        
        layout.addStretch()
        
        # ===== SALDO DE CARTOLETAS =====
        saldo_container = QFrame()
        saldo_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d1f3d, stop:1 #1a1a1a);
                border: 1px solid #9b59b6;
                border-radius: 8px;
                padding: 2px;
            }
        """)
        saldo_layout = QHBoxLayout(saldo_container)
        saldo_layout.setContentsMargins(8, 2, 8, 2)
        
        lbl_saldo = QLabel("💰 Saldo:")
        lbl_saldo.setStyleSheet("font-size: 12px; color: #bb86fc; font-weight: bold; border: none;")
        saldo_layout.addWidget(lbl_saldo)
        
        self.spin_saldo_principal = QDoubleSpinBox()
        self.spin_saldo_principal.setRange(0, 999)
        self.spin_saldo_principal.setValue(100)
        self.spin_saldo_principal.setPrefix("C$ ")
        self.spin_saldo_principal.setSingleStep(5)
        self.spin_saldo_principal.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #1a1a1a;
                border: 1px solid #bb86fc;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
                font-weight: bold;
                color: #00ff88;
                min-width: 90px;
            }
            QDoubleSpinBox:hover {
                border-color: #e0aaff;
            }
        """)
        self.spin_saldo_principal.valueChanged.connect(self.sincronizar_saldo)
        saldo_layout.addWidget(self.spin_saldo_principal)
        
        layout.addWidget(saldo_container)
        
        layout.addSpacing(10)
        
        # Info do mercado
        self.lbl_rodada = QLabel("Rodada: --")
        self.lbl_rodada.setStyleSheet("font-size: 12px; color: #bb86fc;")
        layout.addWidget(self.lbl_rodada)
        
        self.lbl_status_mercado = QLabel("Mercado: --")
        self.lbl_status_mercado.setStyleSheet("font-size: 12px; color: #00ff88;")
        layout.addWidget(self.lbl_status_mercado)
        
        # Botão atualizar
        btn_atualizar = QPushButton("🔄 Atualizar")
        btn_atualizar.clicked.connect(self.carregar_dados)
        layout.addWidget(btn_atualizar)
        
        return header
    
    def sincronizar_saldo(self, valor):
        """Sincroniza o saldo entre todos os campos"""
        # Atualizar campo de cartoletas na aba de escalação
        if hasattr(self, 'spin_cartoletas'):
            self.spin_cartoletas.blockSignals(True)
            self.spin_cartoletas.setValue(valor)
            self.spin_cartoletas.blockSignals(False)
        
        # Atualizar preço máximo no filtro (se quiser filtrar apenas jogadores que cabem no saldo)
        if hasattr(self, 'spin_preco_max'):
            # Não alterar automaticamente o filtro de preço máx, deixar o usuário controlar
            pass
        
        # Recalcular filtro se necessário
        if hasattr(self, 'atletas') and self.atletas:
            self.filtrar_mercado()
    
    def criar_tab_dashboard(self):
        """Cria a aba de dashboard"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Cards de informação
        cards_layout = QHBoxLayout()
        
        # Card: Status
        card_status = QGroupBox("📊 Status do Mercado")
        card_status_layout = QVBoxLayout(card_status)
        self.lbl_mercado_info = QLabel("Carregando...")
        self.lbl_mercado_info.setWordWrap(True)
        self.lbl_mercado_info.setStyleSheet("font-size: 14px;")
        card_status_layout.addWidget(self.lbl_mercado_info)
        cards_layout.addWidget(card_status)
        
        # Card: Estatísticas
        card_stats = QGroupBox("📈 Estatísticas")
        card_stats_layout = QVBoxLayout(card_stats)
        self.lbl_stats = QLabel("Carregando...")
        self.lbl_stats.setWordWrap(True)
        self.lbl_stats.setStyleSheet("font-size: 14px;")
        card_stats_layout.addWidget(self.lbl_stats)
        cards_layout.addWidget(card_stats)
        
        # Card: Destaques
        card_destaques = QGroupBox("⭐ Destaques da Rodada")
        card_destaques_layout = QVBoxLayout(card_destaques)
        self.lbl_destaques = QLabel("Carregando...")
        self.lbl_destaques.setWordWrap(True)
        self.lbl_destaques.setStyleSheet("font-size: 14px;")
        card_destaques_layout.addWidget(self.lbl_destaques)
        cards_layout.addWidget(card_destaques)
        
        layout.addLayout(cards_layout)
        
        # Próximos jogos
        grupo_jogos = QGroupBox("⚽ Próximos Jogos da Rodada")
        jogos_layout = QVBoxLayout(grupo_jogos)
        self.tabela_jogos = QTableWidget()
        self.tabela_jogos.setColumnCount(4)
        self.tabela_jogos.setHorizontalHeaderLabels(["Mandante", "Visitante", "Data/Hora", "Local"])
        self.tabela_jogos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_jogos.setAlternatingRowColors(True)
        jogos_layout.addWidget(self.tabela_jogos)
        layout.addWidget(grupo_jogos)
        
        return tab
    
    def criar_tab_mercado(self):
        """Cria a aba de mercado de atletas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Filtros
        filtros = QGroupBox("🔍 Filtros")
        filtros_layout = QHBoxLayout(filtros)
        
        # Filtro: Posição
        filtros_layout.addWidget(QLabel("Posição:"))
        self.combo_posicao = QComboBox()
        self.combo_posicao.addItem("Todas", 0)
        for pos_id, pos_nome in POSICOES.items():
            self.combo_posicao.addItem(pos_nome, pos_id)
        self.combo_posicao.currentIndexChanged.connect(self.filtrar_mercado)
        filtros_layout.addWidget(self.combo_posicao)
        
        # Filtro: Clube
        filtros_layout.addWidget(QLabel("Clube:"))
        self.combo_clube = QComboBox()
        self.combo_clube.addItem("Todos", 0)
        self.combo_clube.currentIndexChanged.connect(self.filtrar_mercado)
        filtros_layout.addWidget(self.combo_clube)
        
        # Filtro: Preço máximo
        filtros_layout.addWidget(QLabel("Preço máx:"))
        self.spin_preco_max = QDoubleSpinBox()
        self.spin_preco_max.setRange(0, 100)
        self.spin_preco_max.setValue(100)
        self.spin_preco_max.setSingleStep(1)
        self.spin_preco_max.setPrefix("C$ ")
        self.spin_preco_max.valueChanged.connect(self.filtrar_mercado)
        filtros_layout.addWidget(self.spin_preco_max)
        
        # Checkbox: Filtrar pelo saldo
        self.chk_filtrar_saldo = QCheckBox("Cabe no saldo")
        self.chk_filtrar_saldo.setChecked(False)
        self.chk_filtrar_saldo.setToolTip("Mostrar apenas jogadores que cabem no saldo disponível")
        self.chk_filtrar_saldo.stateChanged.connect(self.filtrar_mercado)
        filtros_layout.addWidget(self.chk_filtrar_saldo)
        
        # Filtro: Média mínima
        filtros_layout.addWidget(QLabel("Média mín:"))
        self.spin_media_min = QDoubleSpinBox()
        self.spin_media_min.setRange(0, 20)
        self.spin_media_min.setValue(0)
        self.spin_media_min.setSingleStep(0.5)
        self.spin_media_min.valueChanged.connect(self.filtrar_mercado)
        filtros_layout.addWidget(self.spin_media_min)
        
        # Filtro: Busca por nome
        filtros_layout.addWidget(QLabel("Buscar:"))
        self.txt_busca = QLineEdit()
        self.txt_busca.setPlaceholderText("Nome do atleta...")
        self.txt_busca.textChanged.connect(self.filtrar_mercado)
        filtros_layout.addWidget(self.txt_busca)
        
        # Checkbox: Apenas prováveis
        self.chk_provaveis = QCheckBox("Apenas prováveis")
        self.chk_provaveis.setChecked(True)
        self.chk_provaveis.stateChanged.connect(self.filtrar_mercado)
        filtros_layout.addWidget(self.chk_provaveis)
        
        # Checkbox: Apenas mandantes
        self.chk_mandantes = QCheckBox("Mandantes")
        self.chk_mandantes.setChecked(False)
        self.chk_mandantes.stateChanged.connect(self.filtrar_mercado)
        filtros_layout.addWidget(self.chk_mandantes)
        
        filtros_layout.addStretch()
        layout.addWidget(filtros)
        
        # Info do filtro
        self.lbl_filtro_info = QLabel("Mostrando 0 atletas")
        self.lbl_filtro_info.setStyleSheet("color: #00d9ff; font-size: 12px;")
        layout.addWidget(self.lbl_filtro_info)
        
        # Tabela de atletas
        self.tabela_mercado = QTableWidget()
        self.tabela_mercado.setColumnCount(12)
        self.tabela_mercado.setHorizontalHeaderLabels([
            "Nome", "Posição", "Clube", "Adversário", "Preço", "Média", 
            "Variação", "Jogos", "Score IA", "Confronto", "Status", "Ação"
        ])
        self.tabela_mercado.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_mercado.setAlternatingRowColors(True)
        self.tabela_mercado.setSortingEnabled(True)
        layout.addWidget(self.tabela_mercado)
        
        return tab
    
    def criar_tab_escalacao(self):
        """Cria a aba de escalação inteligente"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Configurações de escalação
        config = QGroupBox("⚙️ Configurações de Escalação")
        config_layout = QGridLayout(config)
        
        # Linha 1: Cartoletas e Esquema
        config_layout.addWidget(QLabel("Cartoletas:"), 0, 0)
        self.spin_cartoletas = QDoubleSpinBox()
        self.spin_cartoletas.setRange(0, 999)
        self.spin_cartoletas.setValue(100)
        self.spin_cartoletas.setPrefix("C$ ")
        self.spin_cartoletas.valueChanged.connect(self.sincronizar_saldo_inverso)
        config_layout.addWidget(self.spin_cartoletas, 0, 1)
        
        config_layout.addWidget(QLabel("Esquema Tático:"), 0, 2)
        self.combo_esquema = QComboBox()
        self.combo_esquema.addItems([
            "4-4-2 🎯 (GOL+2LAT+2ZAG+4MEI+2ATA+TEC)"
        ])
        self.combo_esquema.setEnabled(False)  # Esquema fixo
        self.combo_esquema.setToolTip("Formação fixa: 1 GOL, 2 LAT, 2 ZAG, 4 MEI, 2 ATA, 1 TEC")
        config_layout.addWidget(self.combo_esquema, 0, 3)
        
        # Linha 2: Prioridade e Estratégia
        config_layout.addWidget(QLabel("Prioridade IA:"), 1, 0)
        self.combo_prioridade = QComboBox()
        self.combo_prioridade.addItems([
            "🎯 Equilibrado (Recomendado)",
            "⚽ Máxima Pontuação",
            "💰 Melhor Custo-Benefício",
            "📈 Jogadores em Alta",
            "🏠 Priorizar Mandantes",
            "🎰 Modo Mito (Arriscado)"
        ])
        config_layout.addWidget(self.combo_prioridade, 1, 1)
        
        config_layout.addWidget(QLabel("Risco:"), 1, 2)
        self.slider_risco = QSlider(Qt.Horizontal)
        self.slider_risco.setRange(1, 10)
        self.slider_risco.setValue(5)
        self.slider_risco.setTickPosition(QSlider.TicksBelow)
        config_layout.addWidget(self.slider_risco, 1, 3)
        
        self.lbl_risco = QLabel("Médio")
        self.slider_risco.valueChanged.connect(self.atualizar_label_risco)
        config_layout.addWidget(self.lbl_risco, 1, 4)
        
        # Linha 3: Checkboxes
        self.chk_considerar_confronto = QCheckBox("Considerar força do confronto")
        self.chk_considerar_confronto.setChecked(True)
        config_layout.addWidget(self.chk_considerar_confronto, 2, 0, 1, 2)
        
        self.chk_priorizar_mandantes = QCheckBox("Priorizar jogadores mandantes")
        self.chk_priorizar_mandantes.setChecked(False)
        config_layout.addWidget(self.chk_priorizar_mandantes, 2, 2, 1, 2)
        
        # Checkbox para gerar reservas
        self.chk_gerar_reservas = QCheckBox("🏆 Gerar Reservas de Luxo (mais baratas)")
        self.chk_gerar_reservas.setChecked(True)
        self.chk_gerar_reservas.setStyleSheet("font-size: 11px; color: #a29bfe;")
        config_layout.addWidget(self.chk_gerar_reservas, 3, 0, 1, 2)
        
        # Label informativo sobre reservas
        lbl_reservas_info = QLabel("📝 5 reservas: GOL, LAT, ZAG, MEI, ATA")
        lbl_reservas_info.setStyleSheet("font-size: 10px; color: #888888;")
        config_layout.addWidget(lbl_reservas_info, 3, 2, 1, 2)
        
        # Botão de escalar
        btn_escalar = QPushButton("⚡ ESCALAR TIME COM IA AVANÇADA")
        btn_escalar.setObjectName("btnEscalar")
        btn_escalar.clicked.connect(self.escalar_automaticamente)
        config_layout.addWidget(btn_escalar, 4, 0, 1, 5)
        
        layout.addWidget(config)
        
        # Resultado da escalação
        resultado = QGroupBox("🏆 Escalação Recomendada pela IA")
        resultado_layout = QVBoxLayout(resultado)
        
        # Info da escalação
        info_layout = QHBoxLayout()
        self.lbl_total_gasto = QLabel("Total: C$ 0.00")
        self.lbl_total_gasto.setObjectName("valorTotal")
        info_layout.addWidget(self.lbl_total_gasto)
        
        self.lbl_media_esperada = QLabel("Média esperada: 0.00 pts")
        self.lbl_media_esperada.setStyleSheet("font-size: 16px; color: #00d9ff;")
        info_layout.addWidget(self.lbl_media_esperada)
        
        self.lbl_score_ia = QLabel("Score IA: 0.00")
        self.lbl_score_ia.setStyleSheet("font-size: 16px; color: #ff6b6b;")
        info_layout.addWidget(self.lbl_score_ia)
        
        info_layout.addStretch()
        resultado_layout.addLayout(info_layout)
        
        # Tabela da escalação
        self.tabela_escalacao = QTableWidget()
        self.tabela_escalacao.setColumnCount(10)
        self.tabela_escalacao.setHorizontalHeaderLabels([
            "Posição", "Nome", "Clube", "Adversário", "Preço", "Média", 
            "Score IA", "Confronto", "Variação", "Remover"
        ])
        self.tabela_escalacao.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_escalacao.setAlternatingRowColors(True)
        resultado_layout.addWidget(self.tabela_escalacao)
        
        layout.addWidget(resultado)
        
        # ===== SEÇÃO DE RESERVAS DE LUXO =====
        reservas_group = QGroupBox("🏆 Banco de Reservas (GOL, LAT, ZAG, MEI, ATA)")
        reservas_group.setStyleSheet("""
            QGroupBox {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a1a, stop:1 #2d1f3d);
                border: 1px solid #a29bfe;
                border-radius: 10px;
            }
            QGroupBox::title {
                color: #a29bfe;
                font-size: 11px;
            }
        """)
        reservas_layout = QVBoxLayout(reservas_group)
        reservas_layout.setSpacing(4)
        reservas_layout.setContentsMargins(8, 8, 8, 8)
        
        # Info reservas
        reservas_info_layout = QHBoxLayout()
        self.lbl_reservas_info = QLabel("💎 Reservas: 0 jogadores | C$ 0.00")
        self.lbl_reservas_info.setObjectName("valorReserva")
        self.lbl_reservas_info.setStyleSheet("font-size: 12px;")
        reservas_info_layout.addWidget(self.lbl_reservas_info)
        
        self.lbl_reservas_media = QLabel("📊 Média: 0.00 pts")
        self.lbl_reservas_media.setStyleSheet("font-size: 11px; color: #bb86fc;")
        reservas_info_layout.addWidget(self.lbl_reservas_media)
        reservas_info_layout.addStretch()
        
        reservas_layout.addLayout(reservas_info_layout)
        
        # Tabela de reservas
        self.tabela_reservas = QTableWidget()
        self.tabela_reservas.setColumnCount(8)
        self.tabela_reservas.setHorizontalHeaderLabels([
            "Pos", "Nome", "Clube", "Adv", "Preço", "Média",
            "Score", "Trocar"
        ])
        self.tabela_reservas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_reservas.setAlternatingRowColors(True)
        self.tabela_reservas.setMaximumHeight(160)
        self.tabela_reservas.setStyleSheet("""
            QTableWidget {
                background-color: #151515;
                border: 1px solid #a29bfe;
                font-size: 10px;
            }
            QTableWidget::item {
                padding: 2px;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d1f3d, stop:1 #1a1a1a);
                color: #a29bfe;
                padding: 4px;
                font-size: 10px;
            }
        """)
        self.tabela_reservas.verticalHeader().setDefaultSectionSize(28)
        reservas_layout.addWidget(self.tabela_reservas)
        
        layout.addWidget(reservas_group)
        
        return tab
    
    def atualizar_label_risco(self, valor):
        """Atualiza o label do slider de risco"""
        niveis = {1: "Muito Baixo", 2: "Baixo", 3: "Baixo", 4: "Médio-Baixo", 
                  5: "Médio", 6: "Médio-Alto", 7: "Alto", 8: "Alto", 
                  9: "Muito Alto", 10: "MITO 🎰"}
        self.lbl_risco.setText(niveis.get(valor, "Médio"))
    
    def criar_tab_minha_escalacao(self):
        """Cria a aba de escalação manual"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info
        info = QGroupBox("👥 Minha Escalação")
        info_layout = QVBoxLayout(info)
        
        self.lbl_minha_info = QLabel(
            "Aqui você pode montar sua escalação manualmente.\n"
            "Adicione jogadores da aba Mercado clicando em '+' ou use a IA na aba 'Escalação IA'."
        )
        self.lbl_minha_info.setWordWrap(True)
        info_layout.addWidget(self.lbl_minha_info)
        
        # Valor total
        valores_layout = QHBoxLayout()
        self.lbl_meu_total = QLabel("Total gasto: C$ 0.00")
        self.lbl_meu_total.setObjectName("valorTotal")
        valores_layout.addWidget(self.lbl_meu_total)
        
        self.lbl_minha_media = QLabel("Média esperada: 0.00 pts")
        self.lbl_minha_media.setStyleSheet("font-size: 16px; color: #00d9ff;")
        valores_layout.addWidget(self.lbl_minha_media)
        valores_layout.addStretch()
        
        btn_limpar = QPushButton("🗑️ Limpar Escalação")
        btn_limpar.clicked.connect(self.limpar_escalacao)
        valores_layout.addWidget(btn_limpar)
        
        info_layout.addLayout(valores_layout)
        layout.addWidget(info)
        
        # Tabela minha escalação
        self.tabela_minha = QTableWidget()
        self.tabela_minha.setColumnCount(7)
        self.tabela_minha.setHorizontalHeaderLabels([
            "Posição", "Nome", "Clube", "Preço", "Média", "Score", "Remover"
        ])
        self.tabela_minha.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_minha.setAlternatingRowColors(True)
        layout.addWidget(self.tabela_minha)
        
        return tab
    
    def criar_tab_campo_visual(self):
        """Cria a aba com visual de campo de futebol e fotos dos jogadores"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        
        # Container principal com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #0a0a0a; }")
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)
        
        # ========== HEADER DO TIME ==========
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a0a2e, stop:0.5 #2d1f3d, stop:1 #1a0a2e);
                border: 2px solid #bb86fc;
                border-radius: 15px;
                padding: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # Info do time
        self.lbl_time_titulo = QLabel("⚽ MEU TIME - CARTOLA FC")
        self.lbl_time_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #bb86fc;")
        header_layout.addWidget(self.lbl_time_titulo)
        
        header_layout.addStretch()
        
        # Capitão
        capitao_frame = QFrame()
        capitao_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffd700, stop:1 #ff8c00);
                border-radius: 10px;
                padding: 5px;
            }
        """)
        capitao_layout = QVBoxLayout(capitao_frame)
        capitao_layout.setSpacing(2)
        
        lbl_cap = QLabel("👑 CAPITÃO")
        lbl_cap.setStyleSheet("font-size: 11px; font-weight: bold; color: #1a1a1a; text-align: center;")
        lbl_cap.setAlignment(Qt.AlignCenter)
        capitao_layout.addWidget(lbl_cap)
        
        self.lbl_capitao_nome = QLabel("--")
        self.lbl_capitao_nome.setStyleSheet("font-size: 14px; font-weight: bold; color: #1a1a1a;")
        self.lbl_capitao_nome.setAlignment(Qt.AlignCenter)
        capitao_layout.addWidget(self.lbl_capitao_nome)
        
        self.lbl_capitao_pts = QLabel("2x Pontuação")
        self.lbl_capitao_pts.setStyleSheet("font-size: 10px; color: #333;")
        self.lbl_capitao_pts.setAlignment(Qt.AlignCenter)
        capitao_layout.addWidget(self.lbl_capitao_pts)
        
        header_layout.addWidget(capitao_frame)
        
        header_layout.addSpacing(20)
        
        # Estatísticas
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background: transparent;")
        stats_layout = QHBoxLayout(stats_frame)
        
        self.lbl_campo_gasto = QLabel("💰 C$ 0.00")
        self.lbl_campo_gasto.setStyleSheet("font-size: 14px; color: #00ff88; font-weight: bold;")
        stats_layout.addWidget(self.lbl_campo_gasto)
        
        stats_layout.addSpacing(15)
        
        self.lbl_campo_media = QLabel("📊 0.00 pts")
        self.lbl_campo_media.setStyleSheet("font-size: 14px; color: #00d9ff; font-weight: bold;")
        stats_layout.addWidget(self.lbl_campo_media)
        
        stats_layout.addSpacing(15)
        
        self.lbl_campo_score = QLabel("🎯 Score: 0.00")
        self.lbl_campo_score.setStyleSheet("font-size: 14px; color: #ff6b6b; font-weight: bold;")
        stats_layout.addWidget(self.lbl_campo_score)
        
        header_layout.addWidget(stats_frame)
        
        container_layout.addWidget(header_frame)
        
        # ========== CAMPO DE FUTEBOL ==========
        self.campo_frame = QFrame()
        self.campo_frame.setMinimumHeight(500)
        self.campo_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a472a, stop:0.2 #228b22, stop:0.4 #2e8b2e,
                    stop:0.6 #228b22, stop:0.8 #1a472a, stop:1 #145214);
                border: 3px solid #ffffff;
                border-radius: 15px;
            }
        """)
        
        campo_layout = QVBoxLayout(self.campo_frame)
        campo_layout.setSpacing(5)
        campo_layout.setContentsMargins(20, 15, 20, 15)
        
        # ===== TÉCNICO (Topo) =====
        tec_layout = QHBoxLayout()
        tec_layout.addStretch()
        self.card_tec = self.criar_card_jogador("TEC", "Técnico", 6)
        tec_layout.addWidget(self.card_tec)
        tec_layout.addStretch()
        campo_layout.addLayout(tec_layout)
        
        campo_layout.addSpacing(10)
        
        # ===== ATACANTES (2) =====
        ata_layout = QHBoxLayout()
        ata_layout.addStretch()
        self.card_ata1 = self.criar_card_jogador("ATA", "Atacante 1", 5)
        ata_layout.addWidget(self.card_ata1)
        ata_layout.addSpacing(60)
        self.card_ata2 = self.criar_card_jogador("ATA", "Atacante 2", 5)
        ata_layout.addWidget(self.card_ata2)
        ata_layout.addStretch()
        campo_layout.addLayout(ata_layout)
        
        campo_layout.addSpacing(10)
        
        # ===== MEIAS (4) =====
        mei_layout = QHBoxLayout()
        mei_layout.addStretch()
        self.card_mei1 = self.criar_card_jogador("MEI", "Meia 1", 4)
        mei_layout.addWidget(self.card_mei1)
        mei_layout.addSpacing(25)
        self.card_mei2 = self.criar_card_jogador("MEI", "Meia 2", 4)
        mei_layout.addWidget(self.card_mei2)
        mei_layout.addSpacing(25)
        self.card_mei3 = self.criar_card_jogador("MEI", "Meia 3", 4)
        mei_layout.addWidget(self.card_mei3)
        mei_layout.addSpacing(25)
        self.card_mei4 = self.criar_card_jogador("MEI", "Meia 4", 4)
        mei_layout.addWidget(self.card_mei4)
        mei_layout.addStretch()
        campo_layout.addLayout(mei_layout)
        
        campo_layout.addSpacing(10)
        
        # ===== DEFESA: LAT - ZAG - ZAG - LAT =====
        def_layout = QHBoxLayout()
        def_layout.addStretch()
        self.card_lat1 = self.criar_card_jogador("LAT", "Lateral E", 2)
        def_layout.addWidget(self.card_lat1)
        def_layout.addSpacing(25)
        self.card_zag1 = self.criar_card_jogador("ZAG", "Zagueiro 1", 3)
        def_layout.addWidget(self.card_zag1)
        def_layout.addSpacing(25)
        self.card_zag2 = self.criar_card_jogador("ZAG", "Zagueiro 2", 3)
        def_layout.addWidget(self.card_zag2)
        def_layout.addSpacing(25)
        self.card_lat2 = self.criar_card_jogador("LAT", "Lateral D", 2)
        def_layout.addWidget(self.card_lat2)
        def_layout.addStretch()
        campo_layout.addLayout(def_layout)
        
        campo_layout.addSpacing(10)
        
        # ===== GOLEIRO =====
        gol_layout = QHBoxLayout()
        gol_layout.addStretch()
        self.card_gol = self.criar_card_jogador("GOL", "Goleiro", 1)
        gol_layout.addWidget(self.card_gol)
        gol_layout.addStretch()
        campo_layout.addLayout(gol_layout)
        
        container_layout.addWidget(self.campo_frame)
        
        # ========== BANCO DE RESERVAS ==========
        reservas_frame = QFrame()
        reservas_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a1a1a, stop:0.5 #2d1f3d, stop:1 #1a1a1a);
                border: 2px solid #a29bfe;
                border-radius: 12px;
                padding: 10px;
            }
        """)
        reservas_layout = QVBoxLayout(reservas_frame)
        
        # Título reservas
        reservas_titulo = QLabel("🏆 BANCO DE RESERVAS DE LUXO")
        reservas_titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #a29bfe;")
        reservas_titulo.setAlignment(Qt.AlignCenter)
        reservas_layout.addWidget(reservas_titulo)
        
        # Info reservas
        self.lbl_reservas_visual = QLabel("💎 Reservas mais baratas que titulares | Prontas para entrar!")
        self.lbl_reservas_visual.setStyleSheet("font-size: 11px; color: #888; text-align: center;")
        self.lbl_reservas_visual.setAlignment(Qt.AlignCenter)
        reservas_layout.addWidget(self.lbl_reservas_visual)
        
        # Cards dos reservas
        reservas_cards_layout = QHBoxLayout()
        reservas_cards_layout.addStretch()
        
        self.card_res_gol = self.criar_card_reserva("GOL", 1)
        reservas_cards_layout.addWidget(self.card_res_gol)
        reservas_cards_layout.addSpacing(15)
        
        self.card_res_lat = self.criar_card_reserva("LAT", 2)
        reservas_cards_layout.addWidget(self.card_res_lat)
        reservas_cards_layout.addSpacing(15)
        
        self.card_res_zag = self.criar_card_reserva("ZAG", 3)
        reservas_cards_layout.addWidget(self.card_res_zag)
        reservas_cards_layout.addSpacing(15)
        
        self.card_res_mei = self.criar_card_reserva("MEI", 4)
        reservas_cards_layout.addWidget(self.card_res_mei)
        reservas_cards_layout.addSpacing(15)
        
        self.card_res_ata = self.criar_card_reserva("ATA", 5)
        reservas_cards_layout.addWidget(self.card_res_ata)
        
        reservas_cards_layout.addStretch()
        reservas_layout.addLayout(reservas_cards_layout)
        
        container_layout.addWidget(reservas_frame)
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        return tab
    
    def criar_card_jogador(self, posicao_abrev, nome_default, pos_id):
        """Cria um card de jogador para o campo visual"""
        card = QFrame()
        card.setFixedSize(95, 110)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d2d2d, stop:1 #1a1a1a);
                border: 2px solid #9b59b6;
                border-radius: 10px;
            }
            QFrame:hover {
                border-color: #bb86fc;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d3d3d, stop:1 #2a2a2a);
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(2)
        card_layout.setContentsMargins(5, 5, 5, 5)
        
        # Posição
        lbl_pos = QLabel(posicao_abrev)
        lbl_pos.setAlignment(Qt.AlignCenter)
        lbl_pos.setStyleSheet(f"""
            font-size: 10px;
            font-weight: bold;
            color: #bb86fc;
            background: #1a0a2e;
            border-radius: 3px;
            padding: 1px;
        """)
        card_layout.addWidget(lbl_pos)
        
        # Foto placeholder
        lbl_foto = QLabel("👤")
        lbl_foto.setAlignment(Qt.AlignCenter)
        lbl_foto.setStyleSheet("font-size: 28px; background: transparent;")
        lbl_foto.setObjectName(f"foto_{posicao_abrev}_{pos_id}")
        card_layout.addWidget(lbl_foto)
        
        # Nome
        lbl_nome = QLabel("--")
        lbl_nome.setAlignment(Qt.AlignCenter)
        lbl_nome.setStyleSheet("font-size: 9px; font-weight: bold; color: white;")
        lbl_nome.setObjectName(f"nome_{posicao_abrev}_{pos_id}")
        lbl_nome.setWordWrap(True)
        card_layout.addWidget(lbl_nome)
        
        # Preço/Info
        lbl_info = QLabel("C$ --")
        lbl_info.setAlignment(Qt.AlignCenter)
        lbl_info.setStyleSheet("font-size: 9px; color: #00ff88;")
        lbl_info.setObjectName(f"info_{posicao_abrev}_{pos_id}")
        card_layout.addWidget(lbl_info)
        
        # Guardar referência do pos_id
        card.setProperty("pos_id", pos_id)
        card.setProperty("posicao", posicao_abrev)
        
        return card
    
    def criar_card_reserva(self, posicao_abrev, pos_id):
        """Cria um card de reserva"""
        card = QFrame()
        card.setFixedSize(85, 95)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d1f3d, stop:1 #1a1a1a);
                border: 1px solid #a29bfe;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #bb86fc;
                border-width: 2px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(1)
        card_layout.setContentsMargins(4, 4, 4, 4)
        
        # Posição
        lbl_pos = QLabel(posicao_abrev)
        lbl_pos.setAlignment(Qt.AlignCenter)
        lbl_pos.setStyleSheet("""
            font-size: 9px;
            font-weight: bold;
            color: #a29bfe;
            background: #1a0a2e;
            border-radius: 3px;
        """)
        card_layout.addWidget(lbl_pos)
        
        # Emoji
        lbl_foto = QLabel("🔄")
        lbl_foto.setAlignment(Qt.AlignCenter)
        lbl_foto.setStyleSheet("font-size: 22px; background: transparent;")
        lbl_foto.setObjectName(f"foto_res_{posicao_abrev}")
        card_layout.addWidget(lbl_foto)
        
        # Nome
        lbl_nome = QLabel("--")
        lbl_nome.setAlignment(Qt.AlignCenter)
        lbl_nome.setStyleSheet("font-size: 8px; font-weight: bold; color: #ddd;")
        lbl_nome.setObjectName(f"nome_res_{posicao_abrev}")
        lbl_nome.setWordWrap(True)
        card_layout.addWidget(lbl_nome)
        
        # Preço
        lbl_preco = QLabel("C$ --")
        lbl_preco.setAlignment(Qt.AlignCenter)
        lbl_preco.setStyleSheet("font-size: 8px; color: #a29bfe;")
        lbl_preco.setObjectName(f"preco_res_{posicao_abrev}")
        card_layout.addWidget(lbl_preco)
        
        return card
    
    def criar_tab_analises(self):
        """Cria a aba de análises"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Top jogadores por posição
        grupo_top = QGroupBox("🏅 Top 5 Jogadores por Posição (Melhor Custo-Benefício)")
        top_layout = QVBoxLayout(grupo_top)
        
        self.txt_analise = QTextEdit()
        self.txt_analise.setReadOnly(True)
        self.txt_analise.setStyleSheet("font-family: 'Consolas', monospace; font-size: 13px;")
        top_layout.addWidget(self.txt_analise)
        
        layout.addWidget(grupo_top)
        
        # Dicas
        grupo_dicas = QGroupBox("💡 Dicas da IA")
        dicas_layout = QVBoxLayout(grupo_dicas)
        
        self.txt_dicas = QTextEdit()
        self.txt_dicas.setReadOnly(True)
        self.txt_dicas.setMaximumHeight(200)
        dicas_layout.addWidget(self.txt_dicas)
        
        layout.addWidget(grupo_dicas)
        
        return tab
    
    def criar_tab_confrontos(self):
        """Cria a nova aba de análise de confrontos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo de análise de confrontos
        grupo_confrontos = QGroupBox("⚔️ Análise de Confrontos da Rodada")
        confrontos_layout = QVBoxLayout(grupo_confrontos)
        
        # Tabela de confrontos
        self.tabela_confrontos = QTableWidget()
        self.tabela_confrontos.setColumnCount(8)
        self.tabela_confrontos.setHorizontalHeaderLabels([
            "Mandante", "Visitante", "Local", "Data/Hora",
            "Pot. Gols Casa", "Pot. Gols Fora", "% SG Casa", "% SG Fora"
        ])
        self.tabela_confrontos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_confrontos.setAlternatingRowColors(True)
        confrontos_layout.addWidget(self.tabela_confrontos)
        
        layout.addWidget(grupo_confrontos)
        
        # Grupo de recomendações
        grupo_reco = QGroupBox("🎯 Recomendações por Confronto")
        reco_layout = QVBoxLayout(grupo_reco)
        
        self.txt_recomendacoes = QTextEdit()
        self.txt_recomendacoes.setReadOnly(True)
        self.txt_recomendacoes.setStyleSheet("font-family: 'Consolas', monospace; font-size: 13px;")
        reco_layout.addWidget(self.txt_recomendacoes)
        
        layout.addWidget(grupo_reco)
        
        return tab
    
    def carregar_dados(self):
        """Inicia o carregamento de dados da API"""
        self.status_bar.setText("🔄 Carregando dados da API do Cartola FC...")
        
        # Criar progress dialog
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.statusBar().addWidget(self.progress)
        
        # Iniciar thread
        self.thread = CarregadorDados()
        self.thread.progresso.connect(self.atualizar_progresso)
        self.thread.finalizado.connect(self.dados_carregados)
        self.thread.erro.connect(self.erro_carregamento)
        self.thread.start()
    
    def sincronizar_saldo_inverso(self, valor):
        """Sincroniza o saldo do campo de escalação para o principal"""
        if hasattr(self, 'spin_saldo_principal'):
            self.spin_saldo_principal.blockSignals(True)
            self.spin_saldo_principal.setValue(valor)
            self.spin_saldo_principal.blockSignals(False)
    
    def atualizar_progresso(self, valor):
        """Atualiza a barra de progresso"""
        self.progress.setValue(valor)
    
    def dados_carregados(self, dados):
        """Processa os dados carregados"""
        self.dados = dados
        self.statusBar().removeWidget(self.progress)
        
        # Processar clubes
        self.clubes = dados.get("clubes", {})
        
        # Processar atletas
        mercado = dados.get("mercado", {})
        atletas_raw = mercado.get("atletas", [])
        
        # Normalizar dados dos atletas (API pode usar nomes diferentes)
        self.atletas = []
        for atleta in atletas_raw:
            atleta_normalizado = atleta.copy()
            
            # Normalizar preço (pode vir como 'preco_num' ou 'preco')
            if "preco_num" not in atleta_normalizado or atleta_normalizado.get("preco_num") is None:
                atleta_normalizado["preco_num"] = float(atleta.get("preco", 0) or 0)
            
            # Normalizar média (pode vir como 'media_num' ou 'media')
            if "media_num" not in atleta_normalizado or atleta_normalizado.get("media_num") is None:
                atleta_normalizado["media_num"] = float(atleta.get("media", 0) or 0)
            
            # Normalizar variação (pode vir como 'variacao_num' ou 'variacao')
            if "variacao_num" not in atleta_normalizado or atleta_normalizado.get("variacao_num") is None:
                atleta_normalizado["variacao_num"] = float(atleta.get("variacao", 0) or 0)
            
            # Normalizar jogos (pode vir como 'jogos_num' ou 'jogos')
            if "jogos_num" not in atleta_normalizado or atleta_normalizado.get("jogos_num") is None:
                atleta_normalizado["jogos_num"] = int(atleta.get("jogos", 0) or 0)
            
            # Normalizar pontos (pode vir como 'pontos_num' ou 'pontos')
            if "pontos_num" not in atleta_normalizado or atleta_normalizado.get("pontos_num") is None:
                atleta_normalizado["pontos_num"] = float(atleta.get("pontos", 0) or 0)
            
            # Garantir que campos numéricos são números
            atleta_normalizado["preco_num"] = float(atleta_normalizado.get("preco_num", 0) or 0)
            atleta_normalizado["media_num"] = float(atleta_normalizado.get("media_num", 0) or 0)
            atleta_normalizado["variacao_num"] = float(atleta_normalizado.get("variacao_num", 0) or 0)
            atleta_normalizado["jogos_num"] = int(atleta_normalizado.get("jogos_num", 0) or 0)
            
            self.atletas.append(atleta_normalizado)
        
        # Processar partidas
        self.partidas = dados.get("partidas", {}).get("partidas", [])
        
        # Mapear confrontos para cada clube
        self.confrontos_map = {}
        for partida in self.partidas:
            casa_id = partida.get("clube_casa_id")
            fora_id = partida.get("clube_visitante_id")
            if casa_id and fora_id:
                self.confrontos_map[casa_id] = {"adversario": fora_id, "mandante": True}
                self.confrontos_map[fora_id] = {"adversario": casa_id, "mandante": False}
        
        # Atualizar combo de clubes
        self.combo_clube.clear()
        self.combo_clube.addItem("Todos", 0)
        clubes_ordenados = sorted(self.clubes.items(), key=lambda x: x[1].get("nome", ""))
        for clube_id, clube_data in clubes_ordenados:
            nome = clube_data.get("nome", "?")
            if nome != "OUT":
                self.combo_clube.addItem(nome, int(clube_id))
        
        # Atualizar interface
        self.atualizar_status_mercado()
        self.atualizar_dashboard()
        self.atualizar_tabela_mercado()
        self.atualizar_confrontos()
        self.atualizar_analises()
        
        total = len(self.atletas)
        provaveis = len([a for a in self.atletas if a.get("status_id") == 7])
        self.status_bar.setText(f"✅ Dados carregados! {total} atletas ({provaveis} prováveis) | {len(self.partidas)} partidas")
    
    def erro_carregamento(self, mensagem):
        """Trata erros de carregamento"""
        self.statusBar().removeWidget(self.progress)
        self.status_bar.setText(f"❌ {mensagem}")
        QMessageBox.warning(self, "Erro", mensagem)
    
    def atualizar_status_mercado(self):
        """Atualiza informações do mercado"""
        status = self.dados.get("status", {})
        
        rodada = status.get("rodada_atual", "--")
        self.lbl_rodada.setText(f"📅 Rodada: {rodada}")
        
        status_mercado = status.get("status_mercado", 0)
        if status_mercado == 1:
            self.lbl_status_mercado.setText("🟢 Mercado: ABERTO")
            self.lbl_status_mercado.setStyleSheet("font-size: 16px; color: #00ff88;")
        else:
            self.lbl_status_mercado.setText("🔴 Mercado: FECHADO")
            self.lbl_status_mercado.setStyleSheet("font-size: 16px; color: #ff4444;")
    
    def atualizar_dashboard(self):
        """Atualiza a aba dashboard"""
        # Status do mercado
        status = self.dados.get("status", {})
        rodada = status.get("rodada_atual", "--")
        fechamento = status.get("fechamento", {})
        
        info_mercado = f"""
<b>🏆 Rodada Atual:</b> {rodada}<br>
<b>⏰ Fechamento:</b> {fechamento.get('dia', '--')} às {fechamento.get('hora', '--')}<br>
<b>📊 Atletas no Mercado:</b> {len(self.atletas)}<br>
<b>🏟️ Times:</b> {len(self.clubes)}
"""
        self.lbl_mercado_info.setText(info_mercado)
        
        # Estatísticas
        if self.atletas:
            precos = [a.get("preco_num", 0) for a in self.atletas]
            medias = [a.get("media_num", 0) for a in self.atletas if a.get("media_num", 0) > 0]
            
            preco_medio = sum(precos) / len(precos) if precos else 0
            media_geral = sum(medias) / len(medias) if medias else 0
            
            provaveis = len([a for a in self.atletas if a.get("status_id") == 7])
            
            stats = f"""
<b>💰 Preço Médio:</b> C$ {preco_medio:.2f}<br>
<b>📈 Média Geral:</b> {media_geral:.2f} pts<br>
<b>✅ Jogadores Prováveis:</b> {provaveis}<br>
<b>💎 Mais Caro:</b> C$ {max(precos):.2f}<br>
<b>🏷️ Mais Barato:</b> C$ {min(precos):.2f}
"""
            self.lbl_stats.setText(stats)
            
            # Destaques
            top_media = sorted(self.atletas, key=lambda x: x.get("media_num", 0), reverse=True)[:3]
            destaques = "<b>🌟 Top 3 por Média:</b><br>"
            for i, a in enumerate(top_media, 1):
                nome = a.get("apelido", "")
                media = a.get("media_num", 0)
                destaques += f"{i}. {nome}: {media:.2f} pts<br>"
            
            self.lbl_destaques.setText(destaques)
        
        # Jogos
        partidas = self.dados.get("partidas", {}).get("partidas", [])
        self.tabela_jogos.setRowCount(len(partidas))
        
        for i, partida in enumerate(partidas):
            clube_casa_id = str(partida.get("clube_casa_id", ""))
            clube_fora_id = str(partida.get("clube_visitante_id", ""))
            
            mandante = self.clubes.get(clube_casa_id, {}).get("nome", "?")
            visitante = self.clubes.get(clube_fora_id, {}).get("nome", "?")
            
            data = partida.get("partida_data", "")
            local = partida.get("local", "")
            
            self.tabela_jogos.setItem(i, 0, QTableWidgetItem(mandante))
            self.tabela_jogos.setItem(i, 1, QTableWidgetItem(visitante))
            self.tabela_jogos.setItem(i, 2, QTableWidgetItem(data))
            self.tabela_jogos.setItem(i, 3, QTableWidgetItem(local))
    
    def atualizar_tabela_mercado(self):
        """Atualiza a tabela de atletas do mercado"""
        self.filtrar_mercado()
    
    def filtrar_mercado(self):
        """Filtra os atletas do mercado"""
        posicao_filtro = self.combo_posicao.currentData()
        clube_filtro = self.combo_clube.currentData() if hasattr(self, 'combo_clube') else 0
        preco_max = self.spin_preco_max.value()
        media_min = self.spin_media_min.value()
        busca = self.txt_busca.text().lower()
        apenas_provaveis = self.chk_provaveis.isChecked()
        apenas_mandantes = self.chk_mandantes.isChecked() if hasattr(self, 'chk_mandantes') else False
        filtrar_saldo = self.chk_filtrar_saldo.isChecked() if hasattr(self, 'chk_filtrar_saldo') else False
        saldo_disponivel = self.spin_saldo_principal.value() if hasattr(self, 'spin_saldo_principal') else 100
        
        atletas_filtrados = []
        
        for atleta in self.atletas:
            # Filtro de posição
            if posicao_filtro and atleta.get("posicao_id") != posicao_filtro:
                continue
            
            # Filtro de clube
            if clube_filtro and atleta.get("clube_id") != clube_filtro:
                continue
            
            # Filtro de preço
            if atleta.get("preco_num", 0) > preco_max:
                continue
            
            # Filtro pelo saldo disponível
            if filtrar_saldo and atleta.get("preco_num", 0) > saldo_disponivel:
                continue
            
            # Filtro de média
            if atleta.get("media_num", 0) < media_min:
                continue
            
            # Filtro de busca
            if busca and busca not in atleta.get("apelido", "").lower():
                continue
            
            # Filtro de prováveis
            if apenas_provaveis and atleta.get("status_id") != 7:
                continue
            
            # Filtro de mandantes
            if apenas_mandantes:
                clube_id = atleta.get("clube_id")
                confronto = self.confrontos_map.get(clube_id, {})
                if not confronto.get("mandante", False):
                    continue
            
            atletas_filtrados.append(atleta)
        
        # Calcular score para ordenação
        escalador = EscaladorInteligente(atletas_filtrados, self.clubes, self.partidas)
        for atleta in atletas_filtrados:
            atleta["score"] = escalador.calcular_score(atleta)
        
        # Ordenar por score
        atletas_filtrados.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Atualizar label de info com saldo
        saldo_txt = f" | 💰 Saldo: C$ {saldo_disponivel:.2f}" if filtrar_saldo else ""
        self.lbl_filtro_info.setText(f"Mostrando {len(atletas_filtrados)} atletas{saldo_txt}")
        self.lbl_filtro_info.setStyleSheet("color: #bb86fc; font-size: 13px; font-weight: bold;")
        
        # Atualizar tabela
        self.tabela_mercado.setRowCount(len(atletas_filtrados))
        
        for i, atleta in enumerate(atletas_filtrados):
            nome = atleta.get("apelido", "")
            posicao = POSICOES.get(atleta.get("posicao_id", 0), "?")
            clube_id = atleta.get("clube_id")
            clube = self.clubes.get(str(clube_id), {}).get("nome", "?")
            preco = atleta.get("preco_num", 0)
            media = atleta.get("media_num", 0)
            variacao = atleta.get("variacao_num", 0)
            jogos = atleta.get("jogos_num", 0)
            score = atleta.get("score", 0)
            status = atleta.get("status_id", 0)
            
            # Obter adversário
            confronto = self.confrontos_map.get(clube_id, {})
            adversario_id = confronto.get("adversario")
            adversario = self.clubes.get(str(adversario_id), {}).get("nome", "-")
            mandante = confronto.get("mandante", False)
            adversario_txt = f"{'🏠 vs ' if mandante else '✈️ @ '}{adversario}" if adversario != "-" else "-"
            
            # Calcular fator de confronto
            if adversario_id:
                fator = AnalisadorConfronto.calcular_fator_confronto(clube_id, adversario_id, mandante)
                fator_txt = f"{fator:.2f}x"
                if fator >= 1.2:
                    fator_cor = "#00ff88"
                elif fator <= 0.9:
                    fator_cor = "#ff4444"
                else:
                    fator_cor = "#ffaa00"
            else:
                fator_txt = "-"
                fator_cor = "#888888"
            
            status_info = STATUS_ATLETA.get(status, {"emoji": "❓", "cor": "#888888"})
            status_texto = status_info["emoji"]
            
            self.tabela_mercado.setItem(i, 0, QTableWidgetItem(nome))
            self.tabela_mercado.setItem(i, 1, QTableWidgetItem(posicao))
            self.tabela_mercado.setItem(i, 2, QTableWidgetItem(clube))
            self.tabela_mercado.setItem(i, 3, QTableWidgetItem(adversario_txt))
            self.tabela_mercado.setItem(i, 4, QTableWidgetItem(f"C$ {preco:.2f}"))
            self.tabela_mercado.setItem(i, 5, QTableWidgetItem(f"{media:.2f}"))
            
            var_item = QTableWidgetItem(f"{variacao:+.2f}")
            if variacao > 0:
                var_item.setForeground(QColor("#00ff88"))
            elif variacao < 0:
                var_item.setForeground(QColor("#ff4444"))
            self.tabela_mercado.setItem(i, 6, var_item)
            
            self.tabela_mercado.setItem(i, 7, QTableWidgetItem(str(jogos)))
            
            score_item = QTableWidgetItem(f"{score:.2f}")
            score_item.setForeground(QColor("#00d9ff"))
            self.tabela_mercado.setItem(i, 8, score_item)
            
            fator_item = QTableWidgetItem(fator_txt)
            fator_item.setForeground(QColor(fator_cor))
            self.tabela_mercado.setItem(i, 9, fator_item)
            
            self.tabela_mercado.setItem(i, 10, QTableWidgetItem(status_texto))
            
            # Botão adicionar
            btn_add = QPushButton("➕")
            btn_add.setStyleSheet("padding: 5px 10px;")
            btn_add.clicked.connect(lambda checked, a=atleta: self.adicionar_escalacao(a))
            self.tabela_mercado.setCellWidget(i, 11, btn_add)
    
    def escalar_automaticamente(self):
        """Executa a escalação automática com IA avançada"""
        if not self.atletas:
            QMessageBox.warning(self, "Aviso", "Carregue os dados primeiro!")
            return
        
        cartoletas = self.spin_cartoletas.value()
        
        # FORMAÇÃO FIXA: 1 GOL, 2 LAT, 2 ZAG, 4 MEI, 2 ATA, 1 TEC
        esquema = {1: 1, 2: 2, 3: 2, 4: 4, 5: 2, 6: 1}
        
        # Determinar pesos baseados na prioridade
        prioridade_idx = self.combo_prioridade.currentIndex()
        pesos_opcoes = [
            # Equilibrado
            {"media": 0.30, "preco": 0.15, "variacao": 0.10, "jogos": 0.08, "confronto": 0.20, "potencial_gols": 0.12, "consistencia": 0.05},
            # Máxima Pontuação
            {"media": 0.45, "preco": 0.05, "variacao": 0.10, "jogos": 0.05, "confronto": 0.20, "potencial_gols": 0.10, "consistencia": 0.05},
            # Custo-Benefício
            {"media": 0.20, "preco": 0.35, "variacao": 0.10, "jogos": 0.05, "confronto": 0.15, "potencial_gols": 0.10, "consistencia": 0.05},
            # Em Alta
            {"media": 0.20, "preco": 0.10, "variacao": 0.35, "jogos": 0.05, "confronto": 0.15, "potencial_gols": 0.10, "consistencia": 0.05},
            # Mandantes
            {"media": 0.25, "preco": 0.10, "variacao": 0.10, "jogos": 0.05, "confronto": 0.30, "potencial_gols": 0.15, "consistencia": 0.05},
            # Modo Mito
            {"media": 0.15, "preco": 0.05, "variacao": 0.25, "jogos": 0.05, "confronto": 0.25, "potencial_gols": 0.20, "consistencia": 0.05},
        ]
        
        pesos = pesos_opcoes[prioridade_idx]
        
        # Ajustar pelo nível de risco
        risco = self.slider_risco.value()
        if risco > 7:
            pesos["variacao"] *= 1.3
            pesos["confronto"] *= 1.2
            pesos["media"] *= 0.8
        elif risco < 4:
            pesos["media"] *= 1.3
            pesos["consistencia"] *= 1.5
            pesos["variacao"] *= 0.7
        
        # Normalizar pesos
        total_pesos = sum(pesos.values())
        pesos = {k: v/total_pesos for k, v in pesos.items()}
        
        # Executar escalação
        escalador = EscaladorInteligente(self.atletas, self.clubes, self.partidas, cartoletas)
        
        # Recalcular scores com novos pesos
        for atleta in self.atletas:
            atleta["score"] = escalador.calcular_score(atleta, pesos)
        
        escalacao, gasto = escalador.escalar_time(esquema)
        
        self.escalacao_atual = escalacao
        
        # ===== DEFINIR CAPITÃO (jogador com maior score) =====
        if escalacao:
            capitao = max(escalacao, key=lambda x: x.get("score", 0))
            self.capitao_atual = capitao
            capitao["is_capitao"] = True
            # Marcar outros como não-capitão
            for atleta in escalacao:
                if atleta["atleta_id"] != capitao["atleta_id"]:
                    atleta["is_capitao"] = False
        else:
            self.capitao_atual = None
        
        # Atualizar tabela
        self.tabela_escalacao.setRowCount(len(escalacao))
        
        media_total = 0
        score_total = 0
        
        for i, atleta in enumerate(escalacao):
            posicao = POSICOES.get(atleta.get("posicao_id", 0), "?")
            nome = atleta.get("apelido", "")
            is_capitao = atleta.get("is_capitao", False)
            
            # Adicionar coroa se for capitão
            nome_display = f"👑 {nome}" if is_capitao else nome
            
            clube_id = atleta.get("clube_id")
            clube = self.clubes.get(str(clube_id), {}).get("nome", "?")
            preco = atleta.get("preco_num", 0)
            media = atleta.get("media_num", 0)
            score = atleta.get("score", 0)
            variacao = atleta.get("variacao_num", 0)
            
            # Obter adversário
            confronto = self.confrontos_map.get(clube_id, {})
            adversario_id = confronto.get("adversario")
            adversario = self.clubes.get(str(adversario_id), {}).get("nome", "-")
            mandante = confronto.get("mandante", False)
            adversario_txt = f"{'🏠 ' if mandante else '✈️ '}{adversario}" if adversario != "-" else "-"
            
            # Fator de confronto
            if adversario_id:
                fator = AnalisadorConfronto.calcular_fator_confronto(clube_id, adversario_id, mandante)
                fator_txt = f"{fator:.2f}x"
            else:
                fator_txt = "-"
            
            media_total += media
            score_total += score
            
            # Destacar capitão
            pos_item = QTableWidgetItem(posicao)
            nome_item = QTableWidgetItem(nome_display)
            
            if is_capitao:
                nome_item.setForeground(QColor("#ffd700"))
                nome_item.setBackground(QColor("#2d1f00"))
            
            self.tabela_escalacao.setItem(i, 0, pos_item)
            self.tabela_escalacao.setItem(i, 1, nome_item)
            self.tabela_escalacao.setItem(i, 2, QTableWidgetItem(clube))
            self.tabela_escalacao.setItem(i, 3, QTableWidgetItem(adversario_txt))
            self.tabela_escalacao.setItem(i, 4, QTableWidgetItem(f"C$ {preco:.2f}"))
            self.tabela_escalacao.setItem(i, 5, QTableWidgetItem(f"{media:.2f}"))
            
            score_item = QTableWidgetItem(f"{score:.2f}")
            score_item.setForeground(QColor("#00d9ff"))
            self.tabela_escalacao.setItem(i, 6, score_item)
            
            self.tabela_escalacao.setItem(i, 7, QTableWidgetItem(fator_txt))
            
            var_item = QTableWidgetItem(f"{variacao:+.2f}")
            if variacao > 0:
                var_item.setForeground(QColor("#00ff88"))
            elif variacao < 0:
                var_item.setForeground(QColor("#ff4444"))
            self.tabela_escalacao.setItem(i, 8, var_item)
            
            # Botão remover
            btn_rem = QPushButton("❌")
            btn_rem.setStyleSheet("padding: 5px 10px;")
            btn_rem.clicked.connect(lambda checked, idx=i: self.remover_da_escalacao(idx))
            self.tabela_escalacao.setCellWidget(i, 9, btn_rem)
        
        # Atualizar labels
        self.lbl_total_gasto.setText(f"💰 Total: C$ {gasto:.2f} / C$ {cartoletas:.2f}")
        self.lbl_media_esperada.setText(f"📈 Média esperada: {media_total:.2f} pts")
        self.lbl_score_ia.setText(f"🎯 Score IA: {score_total:.2f}")
        
        # Contagem de mandantes
        mandantes = sum(1 for a in escalacao if self.confrontos_map.get(a.get("clube_id"), {}).get("mandante", False))
        
        # ===== GERAR RESERVAS DE LUXO (mais baratas que titulares) =====
        if self.chk_gerar_reservas.isChecked():
            self.gerar_reservas_luxo(escalacao, escalador, pesos)
        
        # ===== ATUALIZAR VISUAL DO CAMPO =====
        self.atualizar_campo_visual()
        
        self.status_bar.setText(
            f"✅ Escalação montada! {len(escalacao)} jogadores | "
            f"C$ {gasto:.2f} gastos | {mandantes} mandantes | "
            f"👑 Capitão: {self.capitao_atual.get('apelido', '--') if self.capitao_atual else '--'}")
    
    def remover_da_escalacao(self, idx):
        """Remove um jogador da escalação"""
        if 0 <= idx < len(self.escalacao_atual):
            del self.escalacao_atual[idx]
            # Re-renderizar a tabela
            self.renderizar_escalacao()
    
    def renderizar_escalacao(self):
        """Re-renderiza a tabela de escalação"""
        self.tabela_escalacao.setRowCount(len(self.escalacao_atual))
        
        gasto = 0
        media_total = 0
        
        for i, atleta in enumerate(self.escalacao_atual):
            posicao = POSICOES.get(atleta.get("posicao_id", 0), "?")
            nome = atleta.get("apelido", "")
            clube_id = str(atleta.get("clube_id", ""))
            clube = self.clubes.get(clube_id, {}).get("nome", "?")
            preco = atleta.get("preco_num", 0)
            media = atleta.get("media_num", 0)
            score = atleta.get("score", 0)
            variacao = atleta.get("variacao_num", 0)
            
            gasto += preco
            media_total += media
            
            self.tabela_escalacao.setItem(i, 0, QTableWidgetItem(posicao))
            self.tabela_escalacao.setItem(i, 1, QTableWidgetItem(nome))
            self.tabela_escalacao.setItem(i, 2, QTableWidgetItem(clube))
            self.tabela_escalacao.setItem(i, 3, QTableWidgetItem(f"C$ {preco:.2f}"))
            self.tabela_escalacao.setItem(i, 4, QTableWidgetItem(f"{media:.2f}"))
            
            score_item = QTableWidgetItem(f"{score:.2f}")
            score_item.setForeground(QColor("#00d9ff"))
            self.tabela_escalacao.setItem(i, 5, score_item)
            
            var_item = QTableWidgetItem(f"{variacao:+.2f}")
            if variacao > 0:
                var_item.setForeground(QColor("#00ff88"))
            elif variacao < 0:
                var_item.setForeground(QColor("#ff4444"))
            self.tabela_escalacao.setItem(i, 6, var_item)
            
            btn_rem = QPushButton("❌")
            btn_rem.setStyleSheet("padding: 5px 10px;")
            btn_rem.clicked.connect(lambda checked, idx=i: self.remover_da_escalacao(idx))
            self.tabela_escalacao.setCellWidget(i, 7, btn_rem)
        
        cartoletas = self.spin_cartoletas.value()
        self.lbl_total_gasto.setText(f"💰 Total: C$ {gasto:.2f} / C$ {cartoletas:.2f}")
        self.lbl_media_esperada.setText(f"📈 Média esperada: {media_total:.2f} pts")
    
    def adicionar_escalacao(self, atleta):
        """Adiciona um jogador à escalação manual"""
        # Verificar se já está na escalação
        if atleta["atleta_id"] in [a["atleta_id"] for a in self.escalacao_atual]:
            QMessageBox.warning(self, "Aviso", "Jogador já está na escalação!")
            return
        
        # Verificar limite de 12 jogadores
        if len(self.escalacao_atual) >= 12:
            QMessageBox.warning(self, "Aviso", "Escalação completa! Remova alguém primeiro.")
            return
        
        self.escalacao_atual.append(atleta)
        self.atualizar_minha_escalacao()
        self.status_bar.setText(f"✅ {atleta.get('apelido')} adicionado à escalação!")
    
    def atualizar_minha_escalacao(self):
        """Atualiza a tabela de minha escalação"""
        self.tabela_minha.setRowCount(len(self.escalacao_atual))
        
        gasto = 0
        media_total = 0
        
        for i, atleta in enumerate(self.escalacao_atual):
            posicao = POSICOES.get(atleta.get("posicao_id", 0), "?")
            nome = atleta.get("apelido", "")
            clube_id = str(atleta.get("clube_id", ""))
            clube = self.clubes.get(clube_id, {}).get("nome", "?")
            preco = atleta.get("preco_num", 0)
            media = atleta.get("media_num", 0)
            score = atleta.get("score", 0)
            
            gasto += preco
            media_total += media
            
            self.tabela_minha.setItem(i, 0, QTableWidgetItem(posicao))
            self.tabela_minha.setItem(i, 1, QTableWidgetItem(nome))
            self.tabela_minha.setItem(i, 2, QTableWidgetItem(clube))
            self.tabela_minha.setItem(i, 3, QTableWidgetItem(f"C$ {preco:.2f}"))
            self.tabela_minha.setItem(i, 4, QTableWidgetItem(f"{media:.2f}"))
            self.tabela_minha.setItem(i, 5, QTableWidgetItem(f"{score:.2f}"))
            
            btn_rem = QPushButton("❌")
            btn_rem.setStyleSheet("padding: 5px 10px;")
            btn_rem.clicked.connect(lambda checked, idx=i: self.remover_minha(idx))
            self.tabela_minha.setCellWidget(i, 6, btn_rem)
        
        self.lbl_meu_total.setText(f"💰 Total gasto: C$ {gasto:.2f}")
        self.lbl_minha_media.setText(f"📈 Média esperada: {media_total:.2f} pts")
    
    def remover_minha(self, idx):
        """Remove jogador da minha escalação"""
        if 0 <= idx < len(self.escalacao_atual):
            del self.escalacao_atual[idx]
            self.atualizar_minha_escalacao()
    
    def limpar_escalacao(self):
        """Limpa a escalação atual"""
        self.escalacao_atual = []
        self.reservas_atual = []
        self.capitao_atual = None
        self.atualizar_minha_escalacao()
        self.tabela_escalacao.setRowCount(0)
        self.tabela_reservas.setRowCount(0)
        self.lbl_total_gasto.setText("💰 Total: C$ 0.00")
        self.lbl_media_esperada.setText("📈 Média esperada: 0.00 pts")
        self.lbl_reservas_info.setText("💎 Reservas: 0 jogadores | C$ 0.00")
        self.lbl_reservas_media.setText("📊 Média: 0.00 pts")
        
        # Limpar visual do campo
        if hasattr(self, 'lbl_capitao_nome'):
            self.lbl_capitao_nome.setText("--")
            self.lbl_campo_gasto.setText("💰 C$ 0.00")
            self.lbl_campo_media.setText("📊 0.00 pts")
            self.lbl_campo_score.setText("🎯 Score: 0.00")
    
    def gerar_reservas_luxo(self, escalacao_principal, escalador, pesos):
        """Gera o banco de reservas com 5 posições fixas: GOL, LAT, ZAG, MEI, ATA
        IMPORTANTE: Reservas devem ser mais baratas que os titulares da mesma posição!"""
        ids_escalados = [a["atleta_id"] for a in escalacao_principal]
        
        # Obter preços dos titulares por posição
        precos_titulares = {}
        for atleta in escalacao_principal:
            pos_id = atleta.get("posicao_id")
            preco = atleta.get("preco_num", 0)
            if pos_id not in precos_titulares:
                precos_titulares[pos_id] = []
            precos_titulares[pos_id].append(preco)
        
        # Pegar o menor preço de cada posição titular como limite
        limite_preco = {}
        for pos_id, precos in precos_titulares.items():
            limite_preco[pos_id] = min(precos)  # Reserva deve ser menor que o titular mais barato
        
        # Reservas fixas: GOL(1), LAT(2), ZAG(3), MEI(4), ATA(5)
        posicoes_reservas = [1, 2, 3, 4, 5]
        reservas = []
        
        # Filtrar atletas válidos não escalados
        atletas_disponiveis = [
            a for a in self.atletas 
            if a.get("status_id") == 7 and a["atleta_id"] not in ids_escalados
        ]
        
        # Recalcular scores
        for atleta in atletas_disponiveis:
            atleta["score"] = escalador.calcular_score(atleta, pesos)
        
        # Para cada posição fixa, pegar o melhor disponível MAIS BARATO que o titular
        for pos_id in posicoes_reservas:
            preco_max = limite_preco.get(pos_id, 999)  # Limite de preço baseado no titular
            
            candidatos = [
                a for a in atletas_disponiveis 
                if a.get("posicao_id") == pos_id 
                and a["atleta_id"] not in [r["atleta_id"] for r in reservas]
                and a.get("preco_num", 0) < preco_max  # MAIS BARATO que o titular!
            ]
            
            # Se não encontrar ninguém mais barato, pegar qualquer um
            if not candidatos:
                candidatos = [
                    a for a in atletas_disponiveis 
                    if a.get("posicao_id") == pos_id 
                    and a["atleta_id"] not in [r["atleta_id"] for r in reservas]
                ]
            
            candidatos.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            if candidatos:
                melhor = candidatos[0]
                # Determinar quem ele substituiria
                titulares_pos = [a for a in escalacao_principal if a.get("posicao_id") == pos_id]
                if titulares_pos:
                    pior_titular = min(titulares_pos, key=lambda x: x.get("score", 0))
                    melhor["substitui"] = pior_titular.get("apelido", "")
                else:
                    melhor["substitui"] = "-"
                reservas.append(melhor)
        
        self.reservas_atual = reservas
        self.atualizar_tabela_reservas()
    
    def atualizar_tabela_reservas(self):
        """Atualiza a tabela de reservas"""
        self.tabela_reservas.setRowCount(len(self.reservas_atual))
        
        gasto_reservas = 0
        media_reservas = 0
        
        for i, atleta in enumerate(self.reservas_atual):
            posicao = POSICOES_ABREV.get(atleta.get("posicao_id", 0), "?")
            nome = atleta.get("apelido", "")
            clube_id = atleta.get("clube_id")
            clube = self.clubes.get(str(clube_id), {}).get("abreviacao", "?")
            preco = atleta.get("preco_num", 0)
            media = atleta.get("media_num", 0)
            score = atleta.get("score", 0)
            
            gasto_reservas += preco
            media_reservas += media
            
            # Adversário
            confronto = self.confrontos_map.get(clube_id, {})
            adversario_id = confronto.get("adversario")
            adversario = self.clubes.get(str(adversario_id), {}).get("abreviacao", "-")
            mandante = confronto.get("mandante", False)
            adversario_txt = f"{'🏠' if mandante else '✈️'}{adversario}" if adversario != "-" else "-"
            
            # Itens da tabela
            pos_item = QTableWidgetItem(posicao)
            pos_item.setForeground(QColor("#a29bfe"))
            self.tabela_reservas.setItem(i, 0, pos_item)
            
            nome_item = QTableWidgetItem(nome[:15] if len(nome) > 15 else nome)
            nome_item.setForeground(QColor("#ffffff"))
            self.tabela_reservas.setItem(i, 1, nome_item)
            
            self.tabela_reservas.setItem(i, 2, QTableWidgetItem(clube))
            self.tabela_reservas.setItem(i, 3, QTableWidgetItem(adversario_txt))
            self.tabela_reservas.setItem(i, 4, QTableWidgetItem(f"{preco:.1f}"))
            self.tabela_reservas.setItem(i, 5, QTableWidgetItem(f"{media:.1f}"))
            
            score_item = QTableWidgetItem(f"{score:.1f}")
            score_item.setForeground(QColor("#bb86fc"))
            self.tabela_reservas.setItem(i, 6, score_item)
            
            # Botão trocar
            btn_trocar = QPushButton("🔄")
            btn_trocar.setObjectName("btnReserva")
            btn_trocar.setStyleSheet("padding: 2px 8px; font-size: 10px;")
            btn_trocar.clicked.connect(lambda checked, idx=i: self.trocar_reserva_titular(idx))
            self.tabela_reservas.setCellWidget(i, 7, btn_trocar)
        
        # Atualizar labels
        self.lbl_reservas_info.setText(f"💎 Reservas: {len(self.reservas_atual)} | C$ {gasto_reservas:.2f}")
        self.lbl_reservas_media.setText(f"📊 Média: {media_reservas:.2f} pts")
    
    def atualizar_campo_visual(self):
        """Atualiza o visual do campo de futebol com os jogadores escalados"""
        if not hasattr(self, 'escalacao_atual') or not self.escalacao_atual:
            return
        
        # Organizar jogadores por posição
        jogadores_por_pos = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
        for atleta in self.escalacao_atual:
            pos_id = atleta.get("posicao_id")
            if pos_id in jogadores_por_pos:
                jogadores_por_pos[pos_id].append(atleta)
        
        # Calcular totais
        gasto_total = sum(a.get("preco_num", 0) for a in self.escalacao_atual)
        media_total = sum(a.get("media_num", 0) for a in self.escalacao_atual)
        score_total = sum(a.get("score", 0) for a in self.escalacao_atual)
        
        # Atualizar header
        self.lbl_campo_gasto.setText(f"💰 C$ {gasto_total:.2f}")
        self.lbl_campo_media.setText(f"📊 {media_total:.2f} pts")
        self.lbl_campo_score.setText(f"🎯 Score: {score_total:.2f}")
        
        # Atualizar capitão
        if hasattr(self, 'capitao_atual') and self.capitao_atual:
            self.lbl_capitao_nome.setText(self.capitao_atual.get("apelido", "--")[:12])
        
        # Mapear cards aos jogadores
        cards_map = {
            # Goleiro
            (1, 0): self.card_gol,
            # Laterais
            (2, 0): self.card_lat1,
            (2, 1): self.card_lat2,
            # Zagueiros
            (3, 0): self.card_zag1,
            (3, 1): self.card_zag2,
            # Meias
            (4, 0): self.card_mei1,
            (4, 1): self.card_mei2,
            (4, 2): self.card_mei3,
            (4, 3): self.card_mei4,
            # Atacantes
            (5, 0): self.card_ata1,
            (5, 1): self.card_ata2,
            # Técnico
            (6, 0): self.card_tec,
        }
        
        # Preencher cards
        for pos_id, jogadores in jogadores_por_pos.items():
            for idx, atleta in enumerate(jogadores):
                card_key = (pos_id, idx)
                if card_key in cards_map:
                    card = cards_map[card_key]
                    self.preencher_card_jogador(card, atleta)
        
        # Atualizar reservas no visual
        self.atualizar_reservas_visual()
    
    def preencher_card_jogador(self, card, atleta):
        """Preenche um card com os dados do jogador"""
        pos_id = atleta.get("posicao_id", 0)
        pos_abrev = POSICOES_ABREV.get(pos_id, "?")
        nome = atleta.get("apelido", "--")
        preco = atleta.get("preco_num", 0)
        clube_id = atleta.get("clube_id")
        clube = self.clubes.get(str(clube_id), {}).get("abreviacao", "")
        is_capitao = atleta.get("is_capitao", False)
        
        # Encontrar labels dentro do card
        for child in card.findChildren(QLabel):
            obj_name = child.objectName()
            
            if "foto" in obj_name:
                # Emoji baseado na posição e se é capitão
                emoji_pos = {1: "🧤", 2: "🦵", 3: "🛡️", 4: "⚽", 5: "⚡", 6: "📋"}
                emoji = "👑" if is_capitao else emoji_pos.get(pos_id, "👤")
                child.setText(emoji)
                child.setStyleSheet(f"font-size: {'32px' if is_capitao else '28px'}; background: transparent;")
            
            elif "nome" in obj_name:
                nome_display = nome[:10] if len(nome) > 10 else nome
                child.setText(nome_display)
                if is_capitao:
                    child.setStyleSheet("font-size: 9px; font-weight: bold; color: #ffd700;")
                else:
                    child.setStyleSheet("font-size: 9px; font-weight: bold; color: white;")
            
            elif "info" in obj_name:
                child.setText(f"C${preco:.1f} | {clube}")
                child.setStyleSheet("font-size: 8px; color: #00ff88;")
        
        # Destacar card do capitão
        if is_capitao:
            card.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4a3500, stop:1 #2d1f00);
                    border: 2px solid #ffd700;
                    border-radius: 10px;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2d2d2d, stop:1 #1a1a1a);
                    border: 2px solid #9b59b6;
                    border-radius: 10px;
                }
                QFrame:hover {
                    border-color: #bb86fc;
                }
            """)
    
    def atualizar_reservas_visual(self):
        """Atualiza os cards de reservas no visual do campo"""
        if not hasattr(self, 'reservas_atual'):
            return
        
        # Mapear cards de reservas
        cards_reservas = {
            1: self.card_res_gol,
            2: self.card_res_lat,
            3: self.card_res_zag,
            4: self.card_res_mei,
            5: self.card_res_ata,
        }
        
        for atleta in self.reservas_atual:
            pos_id = atleta.get("posicao_id")
            if pos_id in cards_reservas:
                card = cards_reservas[pos_id]
                self.preencher_card_reserva(card, atleta)
    
    def preencher_card_reserva(self, card, atleta):
        """Preenche um card de reserva com os dados do jogador"""
        pos_id = atleta.get("posicao_id", 0)
        nome = atleta.get("apelido", "--")
        preco = atleta.get("preco_num", 0)
        
        # Emoji por posição
        emoji_pos = {1: "🧤", 2: "🦵", 3: "🛡️", 4: "⚽", 5: "⚡"}
        
        for child in card.findChildren(QLabel):
            obj_name = child.objectName()
            
            if "foto" in obj_name:
                child.setText(emoji_pos.get(pos_id, "🔄"))
                child.setStyleSheet("font-size: 22px; background: transparent;")
            
            elif "nome" in obj_name:
                nome_display = nome[:8] if len(nome) > 8 else nome
                child.setText(nome_display)
            
            elif "preco" in obj_name:
                child.setText(f"C$ {preco:.1f}")
    
    def trocar_reserva_titular(self, idx_reserva):
        """Troca um reserva por um titular da mesma posição"""
        if idx_reserva >= len(self.reservas_atual):
            return
        
        reserva = self.reservas_atual[idx_reserva]
        pos_reserva = reserva.get("posicao_id")
        
        # Encontrar titular da mesma posição com menor score
        titulares_pos = [a for a in self.escalacao_atual if a.get("posicao_id") == pos_reserva]
        
        if not titulares_pos:
            QMessageBox.warning(self, "Aviso", "Não há titulares dessa posição para trocar!")
            return
        
        pior_titular = min(titulares_pos, key=lambda x: x.get("score", 0))
        
        # Fazer a troca
        idx_titular = self.escalacao_atual.index(pior_titular)
        
        # Trocar
        self.escalacao_atual[idx_titular] = reserva
        self.reservas_atual[idx_reserva] = pior_titular
        pior_titular["substitui"] = reserva.get("apelido", "")
        
        # Atualizar tabelas
        self.renderizar_escalacao()
        self.atualizar_tabela_reservas()
        self.atualizar_minha_escalacao()
        
        self.status_bar.setText(f"🔄 Troca realizada: {reserva.get('apelido')} ↔️ {pior_titular.get('apelido')}")
    
    def atualizar_analises(self):
        """Atualiza a aba de análises"""
        if not self.atletas:
            return
        
        escalador = EscaladorInteligente(self.atletas, self.clubes, self.partidas)
        
        # Calcular scores
        for atleta in self.atletas:
            atleta["score"] = escalador.calcular_score(atleta)
        
        # Top 5 por posição
        analise = "=" * 70 + "\n"
        analise += "🏅 TOP 5 JOGADORES POR POSIÇÃO (Score IA + Análise de Confronto)\n"
        analise += "=" * 70 + "\n\n"
        
        for pos_id, pos_nome in POSICOES.items():
            atletas_pos = [a for a in self.atletas if a.get("posicao_id") == pos_id and a.get("status_id") == 7]
            atletas_pos.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            analise += f"\n📌 {pos_nome.upper()}S:\n"
            analise += "-" * 65 + "\n"
            
            for i, a in enumerate(atletas_pos[:5], 1):
                nome = a.get("apelido", "")[:18].ljust(18)
                clube_id = a.get("clube_id")
                clube = self.clubes.get(str(clube_id), {}).get("abreviacao", "???")
                preco = a.get("preco_num", 0)
                media = a.get("media_num", 0)
                score = a.get("score", 0)
                
                # Adversário
                confronto = self.confrontos_map.get(clube_id, {})
                adversario_id = confronto.get("adversario")
                adversario = self.clubes.get(str(adversario_id), {}).get("abreviacao", "")
                mandante = confronto.get("mandante", False)
                local = "🏠" if mandante else "✈️"
                
                analise += f"  {i}. {nome} ({clube}) {local} {adversario:>4} | C$ {preco:>5.2f} | Média: {media:>5.2f} | Score: {score:>5.2f}\n"
        
        # Custo-benefício
        analise += "\n\n" + "=" * 70 + "\n"
        analise += "💎 MELHORES CUSTO-BENEFÍCIO (Preço < C$ 10)\n"
        analise += "=" * 70 + "\n\n"
        
        baratos = [a for a in self.atletas if a.get("preco_num", 0) < 10 and a.get("status_id") == 7]
        baratos.sort(key=lambda x: x.get("media_num", 0) / max(x.get("preco_num", 0.1), 0.1), reverse=True)
        
        for i, a in enumerate(baratos[:10], 1):
            nome = a.get("apelido", "")[:18].ljust(18)
            pos = POSICOES_ABREV.get(a.get("posicao_id", 0), "???")
            preco = a.get("preco_num", 0)
            media = a.get("media_num", 0)
            cb = media / max(preco, 0.1)
            
            analise += f"  {i}. {nome} ({pos}) | C$ {preco:>5.2f} | Média: {media:>5.2f} | CB: {cb:>5.2f}\n"
        
        # Mandantes com bons confrontos
        analise += "\n\n" + "=" * 70 + "\n"
        analise += "🏠 MANDANTES COM CONFRONTO FAVORÁVEL\n"
        analise += "=" * 70 + "\n\n"
        
        mandantes_favoraveis = []
        for atleta in self.atletas:
            if atleta.get("status_id") != 7:
                continue
            clube_id = atleta.get("clube_id")
            confronto = self.confrontos_map.get(clube_id, {})
            if not confronto.get("mandante", False):
                continue
            adversario_id = confronto.get("adversario")
            if adversario_id:
                fator = AnalisadorConfronto.calcular_fator_confronto(clube_id, adversario_id, True)
                if fator >= 1.15:
                    atleta["fator_confronto"] = fator
                    mandantes_favoraveis.append(atleta)
        
        mandantes_favoraveis.sort(key=lambda x: x.get("score", 0) * x.get("fator_confronto", 1), reverse=True)
        
        for i, a in enumerate(mandantes_favoraveis[:10], 1):
            nome = a.get("apelido", "")[:18].ljust(18)
            pos = POSICOES_ABREV.get(a.get("posicao_id", 0), "???")
            fator = a.get("fator_confronto", 1)
            score = a.get("score", 0)
            
            analise += f"  {i}. {nome} ({pos}) | Fator: {fator:.2f}x | Score: {score:.2f}\n"
        
        self.txt_analise.setText(analise)
        
        # Dicas
        dicas = "💡 DICAS INTELIGENTES PARA ESTA RODADA:\n\n"
        
        # Jogadores em alta
        em_alta = sorted(self.atletas, key=lambda x: x.get("variacao_num", 0), reverse=True)[:5]
        dicas += "📈 Jogadores em ALTA (boa fase, valorizando):\n"
        for a in em_alta:
            nome = a.get("apelido", "")
            var = a.get("variacao_num", 0)
            dicas += f"  • {nome}: +C$ {var:.2f}\n"
        
        dicas += "\n📉 Jogadores em QUEDA (evitar se possível):\n"
        em_queda = sorted(self.atletas, key=lambda x: x.get("variacao_num", 0))[:5]
        for a in em_queda:
            nome = a.get("apelido", "")
            var = a.get("variacao_num", 0)
            dicas += f"  • {nome}: C$ {var:.2f}\n"
        
        dicas += "\n⚽ ESTRATÉGIA RECOMENDADA:\n"
        dicas += "  • Priorize jogadores prováveis (status ✅)\n"
        dicas += "  • Jogadores MANDANTES têm vantagem histórica (+15% pontuação)\n"
        dicas += "  • Confira a coluna 'Confronto' - valores acima de 1.2x são favoráveis\n"
        dicas += "  • Use a IA para otimizar considerando todos os fatores!\n"
        dicas += "  • Equilibre entre jogadores caros (pontuam mais) e baratos (custo-benefício)\n"
        dicas += f"\n🎯 Rodada {self.dados.get('status', {}).get('rodada_atual', '?')}: {len(self.partidas)} jogos\n"
        
        self.txt_dicas.setText(dicas)
    
    def atualizar_confrontos(self):
        """Atualiza a aba de confrontos"""
        if not self.partidas:
            return
        
        self.tabela_confrontos.setRowCount(len(self.partidas))
        
        recomendacoes = "=" * 70 + "\n"
        recomendacoes += "🎯 RECOMENDAÇÕES POR CONFRONTO\n"
        recomendacoes += "=" * 70 + "\n\n"
        
        for i, partida in enumerate(self.partidas):
            casa_id = partida.get("clube_casa_id")
            fora_id = partida.get("clube_visitante_id")
            
            casa = self.clubes.get(str(casa_id), {}).get("nome", "?")
            fora = self.clubes.get(str(fora_id), {}).get("nome", "?")
            local = partida.get("local", "-")
            data = partida.get("partida_data", "-")
            
            # Calcular métricas
            pot_gols_casa = AnalisadorConfronto.calcular_potencial_gols(casa_id, fora_id, True)
            pot_gols_fora = AnalisadorConfronto.calcular_potencial_gols(fora_id, casa_id, False)
            chance_sg_casa = AnalisadorConfronto.calcular_potencial_saldo(casa_id, fora_id, True)
            chance_sg_fora = AnalisadorConfronto.calcular_potencial_saldo(fora_id, casa_id, False)
            
            self.tabela_confrontos.setItem(i, 0, QTableWidgetItem(casa))
            self.tabela_confrontos.setItem(i, 1, QTableWidgetItem(fora))
            self.tabela_confrontos.setItem(i, 2, QTableWidgetItem(local))
            self.tabela_confrontos.setItem(i, 3, QTableWidgetItem(data))
            
            # Potencial de gols (colorido)
            item_gols_casa = QTableWidgetItem(f"{pot_gols_casa:.1f} ⚽")
            if pot_gols_casa >= 2.0:
                item_gols_casa.setForeground(QColor("#00ff88"))
            elif pot_gols_casa <= 1.0:
                item_gols_casa.setForeground(QColor("#ff4444"))
            self.tabela_confrontos.setItem(i, 4, item_gols_casa)
            
            item_gols_fora = QTableWidgetItem(f"{pot_gols_fora:.1f} ⚽")
            if pot_gols_fora >= 1.5:
                item_gols_fora.setForeground(QColor("#00ff88"))
            elif pot_gols_fora <= 0.8:
                item_gols_fora.setForeground(QColor("#ff4444"))
            self.tabela_confrontos.setItem(i, 5, item_gols_fora)
            
            # Chance SG
            item_sg_casa = QTableWidgetItem(f"{chance_sg_casa:.0f}%")
            if chance_sg_casa >= 35:
                item_sg_casa.setForeground(QColor("#00ff88"))
            self.tabela_confrontos.setItem(i, 6, item_sg_casa)
            
            item_sg_fora = QTableWidgetItem(f"{chance_sg_fora:.0f}%")
            if chance_sg_fora >= 25:
                item_sg_fora.setForeground(QColor("#00ff88"))
            self.tabela_confrontos.setItem(i, 7, item_sg_fora)
            
            # Recomendações
            recomendacoes += f"⚔️ {casa} x {fora}\n"
            recomendacoes += "-" * 50 + "\n"
            
            if pot_gols_casa >= 2.0:
                recomendacoes += f"  🔥 ATACANTES/MEIAS do {casa} têm alto potencial de gols!\n"
            if chance_sg_casa >= 40:
                recomendacoes += f"  🛡️ GOL/ZAG do {casa} têm boa chance de SG ({chance_sg_casa:.0f}%)\n"
            if pot_gols_fora >= 1.5:
                recomendacoes += f"  ⚡ ATACANTES do {fora} podem surpreender fora de casa\n"
            if chance_sg_casa < 20:
                recomendacoes += f"  ⚠️ Evite GOL/ZAG do {casa} - defesa vulnerável\n"
            
            recomendacoes += "\n"
        
        self.txt_recomendacoes.setText(recomendacoes)


# ====================== MAIN ======================
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Definir paleta escura com roxo
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(10, 10, 10))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(26, 26, 26))
    palette.setColor(QPalette.AlternateBase, QColor(15, 15, 15))
    palette.setColor(QPalette.ToolTipBase, QColor(45, 31, 61))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(155, 89, 182))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(187, 134, 252))
    palette.setColor(QPalette.Highlight, QColor(155, 89, 182))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    window = CartolaFCManager()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
