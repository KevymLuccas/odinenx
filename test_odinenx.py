#!/usr/bin/env python3
"""
🧪 ODINENX - Script de Testes de Fluxo
=====================================

Este script testa os principais fluxos do sistema:
1. Verificação de páginas públicas
2. API de palpites/jogos
3. SEO e meta tags
4. Estrutura do site

Executar: python test_odinenx.py
"""

import requests
import json
import re
from datetime import datetime

# Configurações
BASE_URL = "https://odinenx.vercel.app"
API_URL = "https://odinenx.vercel.app/api/football"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")

def test_homepage():
    """Testar página inicial"""
    print_header("TESTE 1: Homepage")
    
    try:
        response = requests.get(BASE_URL, timeout=30)
        
        if response.status_code == 200:
            print_success(f"Homepage carregada (Status: {response.status_code})")
            
            # Verificar conteúdo HTML
            html = response.text
            
            # Verificar título SEO
            if "Palpites de Futebol" in html or "ODINENX" in html:
                print_success("Título SEO encontrado")
            else:
                print_error("Título SEO não encontrado")
            
            # Verificar meta description
            if 'meta name="description"' in html:
                print_success("Meta description presente")
            else:
                print_error("Meta description ausente")
            
            # Verificar Open Graph
            if 'og:title' in html:
                print_success("Open Graph tags presentes")
            else:
                print_error("Open Graph tags ausentes")
            
            # Verificar JSON-LD
            if 'application/ld+json' in html:
                print_success("Structured Data (JSON-LD) presente")
            else:
                print_error("Structured Data ausente")
                
            return True
        else:
            print_error(f"Erro ao carregar homepage: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exceção: {str(e)}")
        return False

def test_api_football():
    """Testar API de jogos/palpites"""
    print_header("TESTE 2: API de Palpites")
    
    ligas = [
        ("BSA", "Brasileirão"),
        ("PL", "Premier League"),
        ("PD", "La Liga"),
        ("CL", "Champions League")
    ]
    
    resultados = []
    
    for code, nome in ligas:
        try:
            url = f"{API_URL}?competition={code}&status=SCHEDULED"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if "matches" in data:
                    num_jogos = len(data["matches"])
                    print_success(f"{nome}: {num_jogos} jogos encontrados")
                    resultados.append((nome, num_jogos, True))
                else:
                    print_info(f"{nome}: Sem jogos agendados")
                    resultados.append((nome, 0, True))
            else:
                print_error(f"{nome}: Erro {response.status_code}")
                resultados.append((nome, 0, False))
                
        except Exception as e:
            print_error(f"{nome}: {str(e)}")
            resultados.append((nome, 0, False))
    
    # Resumo
    total_jogos = sum(r[1] for r in resultados)
    sucesso = all(r[2] for r in resultados)
    
    print_info(f"Total de jogos disponíveis: {total_jogos}")
    
    return sucesso

def test_static_files():
    """Testar arquivos estáticos"""
    print_header("TESTE 3: Arquivos Estáticos")
    
    arquivos = [
        "/sitemap.xml",
        "/robots.txt",
        "/logo.webp",
        "/icone.webp"
    ]
    
    sucesso = True
    
    for arquivo in arquivos:
        try:
            response = requests.get(f"{BASE_URL}{arquivo}", timeout=15)
            
            if response.status_code == 200:
                tamanho = len(response.content)
                print_success(f"{arquivo}: OK ({tamanho} bytes)")
            else:
                print_error(f"{arquivo}: Status {response.status_code}")
                sucesso = False
                
        except Exception as e:
            print_error(f"{arquivo}: {str(e)}")
            sucesso = False
    
    return sucesso

def test_seo_elements():
    """Testar elementos SEO importantes"""
    print_header("TESTE 4: SEO Avançado")
    
    try:
        response = requests.get(BASE_URL, timeout=30)
        html = response.text
        
        # Keywords importantes para ranking
        keywords_seo = [
            "palpites",
            "futebol",
            "Brasileirão",
            "apostas",
            "análise",
            "IA"
        ]
        
        print_info("Verificando palavras-chave no conteúdo...")
        
        for keyword in keywords_seo:
            if keyword.lower() in html.lower():
                print_success(f'Keyword "{keyword}" encontrada')
            else:
                print_error(f'Keyword "{keyword}" não encontrada')
        
        # Verificar sitemap
        sitemap_response = requests.get(f"{BASE_URL}/sitemap.xml", timeout=15)
        if sitemap_response.status_code == 200:
            sitemap = sitemap_response.text
            urls_count = sitemap.count("<url>")
            print_success(f"Sitemap válido com {urls_count} URLs")
        else:
            print_error("Sitemap não encontrado")
        
        # Verificar robots.txt
        robots_response = requests.get(f"{BASE_URL}/robots.txt", timeout=15)
        if robots_response.status_code == 200:
            if "Sitemap:" in robots_response.text:
                print_success("robots.txt com referência ao sitemap")
            else:
                print_info("robots.txt sem referência ao sitemap")
        else:
            print_error("robots.txt não encontrado")
        
        return True
        
    except Exception as e:
        print_error(f"Erro no teste SEO: {str(e)}")
        return False

def test_pages():
    """Testar páginas principais"""
    print_header("TESTE 5: Páginas Principais")
    
    paginas = [
        ("/", "Homepage"),
        ("/login", "Login"),
        ("/register", "Registro"),
    ]
    
    sucesso = True
    
    for path, nome in paginas:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=30)
            
            if response.status_code == 200:
                print_success(f"{nome}: Acessível")
            else:
                print_error(f"{nome}: Status {response.status_code}")
                sucesso = False
                
        except Exception as e:
            print_error(f"{nome}: {str(e)}")
            sucesso = False
    
    return sucesso

def gerar_relatorio(resultados):
    """Gerar relatório final"""
    print_header("RELATÓRIO FINAL")
    
    total = len(resultados)
    sucesso = sum(1 for r in resultados if r)
    falhas = total - sucesso
    
    print(f"\n{Colors.BOLD}📊 Resultados:{Colors.END}")
    print(f"   ✓ Testes passaram: {Colors.GREEN}{sucesso}/{total}{Colors.END}")
    
    if falhas > 0:
        print(f"   ✗ Testes falharam: {Colors.RED}{falhas}/{total}{Colors.END}")
    
    taxa = (sucesso / total) * 100
    
    if taxa == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 TODOS OS TESTES PASSARAM! Sistema funcionando corretamente.{Colors.END}")
    elif taxa >= 80:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ MAIORIA DOS TESTES PASSOU. Alguns ajustes podem ser necessários.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ VÁRIOS TESTES FALHARAM. Verificar problemas.{Colors.END}")
    
    print(f"\n{Colors.BLUE}📅 Data do teste: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}{Colors.END}")
    print(f"{Colors.BLUE}🌐 URL testada: {BASE_URL}{Colors.END}")
    print(f"\n{Colors.BOLD}{Colors.YELLOW}🚀 ODINENX está em BETA - Melhorando a cada dia!{Colors.END}\n")

def main():
    """Executar todos os testes"""
    print(f"\n{Colors.BOLD}🔬 ODINENX - Suite de Testes{Colors.END}")
    print(f"{Colors.YELLOW}Sistema em BETA - Testando fluxos principais...{Colors.END}")
    
    resultados = []
    
    # Executar testes
    resultados.append(test_homepage())
    resultados.append(test_api_football())
    resultados.append(test_static_files())
    resultados.append(test_seo_elements())
    resultados.append(test_pages())
    
    # Gerar relatório
    gerar_relatorio(resultados)
    
    # Return code
    if all(resultados):
        return 0
    return 1

if __name__ == "__main__":
    exit(main())
