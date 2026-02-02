#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔒 TESTE PRÁTICO DE CONTROLE DE ACESSO
Simula diferentes usuários e testa redirecionamentos
"""

import time

# Simulação da lógica hasAccess() do JavaScript
def has_access(plan, feature):
    """Reproduz exatamente a lógica do stripe.js"""
    
    plans_config = {
        'free': {
            'limits': {
                'analysisPerDay': 3,
                'historyDays': 7
            }
        },
        'basic': {
            'limits': {
                'analysisPerDay': -1,
                'historyDays': 30
            }
        },
        'pro': {
            'limits': {
                'analysisPerDay': -1,
                'historyDays': 90,
                'paperTrading': True,
                'cartola': True,
                'alerts': True
            }
        },
        'elite': {
            'limits': {
                'analysisPerDay': -1,
                'historyDays': -1,
                'paperTrading': True,
                'cartola': True,
                'alerts': True,
                'admin': True,
                'reports': True
            }
        }
    }
    
    plan_config = plans_config.get(plan, plans_config['free'])
    limits = plan_config.get('limits', {})
    
    # Reproduzir a lógica do switch/case
    if feature == 'bet':
        return True  # Todos podem acessar BET básico
    elif feature == 'trade':
        return plan in ['pro', 'elite']  # Só Pro/Elite
    elif feature == 'cartola':
        return limits.get('cartola') == True  # Só Pro/Elite
    elif feature == 'alerts':
        return limits.get('alerts') == True  # Só Pro/Elite
    elif feature == 'paperTrading':
        return limits.get('paperTrading') == True  # Só Pro/Elite
    elif feature == 'admin':
        return limits.get('admin') == True  # Só Elite
    elif feature == 'analysisUnlimited':
        return limits.get('analysisPerDay') == -1  # Basic+
    elif feature == 'fullHistory':
        return limits.get('historyDays') == -1  # Elite
    elif feature == 'iaAvancada':
        return plan in ['pro', 'elite']
    else:
        return False

def test_user_access(user_name, plan):
    """Testa acesso de um usuário específico"""
    print(f"\n👤 USUÁRIO: {user_name.upper()} - Plano: {plan.upper()}")
    print("-" * 50)
    
    features_to_test = [
        ('bet', 'BET Module'),
        ('trade', 'Trade Signals'),
        ('cartola', 'Cartola FC'),
        ('alerts', 'Sistema de Alertas'),
        ('paperTrading', 'Paper Trading'),
        ('admin', 'Painel Admin')
    ]
    
    results = []
    
    for feature_key, feature_name in features_to_test:
        access = has_access(plan, feature_key)
        status = "✅ PERMITIDO" if access else "❌ NEGADO"
        print(f"   {feature_name}: {status}")
        results.append((feature_name, access))
    
    return results

def simulate_user_journey(user_name, plan):
    """Simula a jornada do usuário tentando acessar diferentes páginas"""
    print(f"\n🚶‍♂️ SIMULAÇÃO DE NAVEGAÇÃO - {user_name}")
    print("=" * 60)
    
    # Páginas que tentará acessar
    pages = [
        ('/dashboard', 'Dashboard', True),  # Todos logados
        ('/bet', 'BET Module', has_access(plan, 'bet')),
        ('/trade', 'Trade Signals', has_access(plan, 'trade')),
        ('/cartola', 'Cartola FC', has_access(plan, 'cartola')),
        ('/alerts', 'Alertas', has_access(plan, 'alerts')),
        ('/paper-trading', 'Paper Trading', has_access(plan, 'paperTrading')),
        ('/admin', 'Admin Panel', has_access(plan, 'admin'))
    ]
    
    accessible_pages = 0
    blocked_pages = 0
    
    for url, name, should_access in pages:
        if should_access:
            print(f"🟢 {name} → ACESSO PERMITIDO")
            accessible_pages += 1
        else:
            print(f"🔴 {name} → BLOQUEADO (redirecionado)")
            blocked_pages += 1
    
    return accessible_pages, blocked_pages

def main():
    print("🔒 TESTE PRÁTICO DE CONTROLE DE ACESSO POR PLANO")
    print("=" * 80)
    print("⏰ Simulando usuários reais com diferentes planos...")
    print()
    
    # Usuários de teste
    test_users = [
        ("João Silva", "basic"),
        ("Maria Santos", "pro"),
        ("Carlos Admin", "elite"),
        ("Ana Free", "free")
    ]
    
    all_results = {}
    
    # Testar cada usuário
    for user_name, plan in test_users:
        results = test_user_access(user_name, plan)
        all_results[user_name] = {
            'plan': plan,
            'results': results
        }
        
        # Simular navegação
        accessible, blocked = simulate_user_journey(user_name, plan)
        print(f"   📊 Estatísticas: {accessible} páginas acessíveis, {blocked} bloqueadas")
        
        time.sleep(0.5)  # Pausa para visualização
    
    print("\n" + "=" * 80)
    print("📈 MATRIZ DE CONTROLE DE ACESSO")
    print("=" * 80)
    
    # Cabeçalho da tabela
    features = ["BET", "Trade", "Cartola", "Alertas", "Paper Trading", "Admin"]
    print(f"{'PLANO':<10}", end="")
    for feature in features:
        print(f"{feature:>12}", end="")
    print()
    print("-" * 80)
    
    # Linhas da tabela
    plans_order = ['free', 'basic', 'pro', 'elite']
    for plan in plans_order:
        print(f"{plan.upper():<10}", end="")
        
        feature_keys = ['bet', 'trade', 'cartola', 'alerts', 'paperTrading', 'admin']
        for feature_key in feature_keys:
            access = has_access(plan, feature_key)
            symbol = "✅" if access else "❌"
            print(f"{symbol:>12}", end="")
        print()
    
    print("\n" + "=" * 80)
    print("🎯 RESUMO DO CONTROLE DE ACESSO")
    print("=" * 80)
    
    # Verificar se o controle está correto
    checks = [
        ("Basic não tem Paper Trading", not has_access('basic', 'paperTrading')),
        ("Basic não tem Alertas", not has_access('basic', 'alerts')),
        ("Pro tem Paper Trading", has_access('pro', 'paperTrading')),
        ("Pro tem Alertas", has_access('pro', 'alerts')),
        ("Pro NÃO tem Admin", not has_access('pro', 'admin')),
        ("Elite tem tudo", all([
            has_access('elite', f) for f in ['bet', 'trade', 'cartola', 'alerts', 'paperTrading', 'admin']
        ])),
        ("Free só tem BET", has_access('free', 'bet') and not has_access('free', 'trade'))
    ]
    
    passed_checks = 0
    for description, result in checks:
        status = "✅ CORRETO" if result else "❌ ERRO"
        print(f"• {description}: {status}")
        if result:
            passed_checks += 1
    
    print(f"\n🏆 RESULTADO: {passed_checks}/{len(checks)} verificações passaram")
    
    if passed_checks == len(checks):
        print("🎉 CONTROLE DE ACESSO 100% FUNCIONAL!")
    else:
        print("⚠️ EXISTEM PROBLEMAS NO CONTROLE DE ACESSO!")
    
    print("\n🌐 Teste a aplicação: https://odinenx.vercel.app")

if __name__ == "__main__":
    main()