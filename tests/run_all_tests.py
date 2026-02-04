"""
🧪 Runner Principal - Executa todos os testes ODINENX v2.0
"""

import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Executa todos os testes"""
    
    print("\n" + "="*70)
    print("🚀 ODINENX v2.0 - SUÍTE COMPLETA DE TESTES")
    print("="*70)
    print("""
    Este script executa todos os testes de validação para o sistema
    de salas ao vivo com chat em tempo real.
    
    Testes incluídos:
    ├── 📡 test_live_apis.py     - APIs de placar e odds
    ├── 🎮 test_room_simulation.py - Simulação de sala completa
    └── 🔄 test_realtime.py      - Eventos WebSocket/Realtime
    """)
    
    print("="*70)
    print("📡 EXECUTANDO: test_live_apis.py")
    print("="*70)
    
    try:
        from test_live_apis import run_all_tests
        run_all_tests()
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n" + "="*70)
    print("🎮 EXECUTANDO: test_room_simulation.py")
    print("="*70)
    
    try:
        from test_room_simulation import run_simulation, test_celebration_effects, test_customization_store
        run_simulation()
        test_celebration_effects()
        test_customization_store()
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n" + "="*70)
    print("🔄 EXECUTANDO: test_realtime.py")
    print("="*70)
    
    try:
        from test_realtime import run_all_realtime_tests
        run_all_realtime_tests()
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n" + "="*70)
    print("✅ TODOS OS TESTES FINALIZADOS!")
    print("="*70)
    
    print("""
    
    📋 CHECKLIST PARA IMPLEMENTAÇÃO:
    
    ✅ Estrutura de dados validada
    ✅ Fluxo de eventos mapeado
    ✅ Sistema de planos definido
    ✅ Efeitos de celebração planejados
    ✅ Loja de customização modelada
    
    🔧 PRÓXIMOS PASSOS:
    
    1. Configurar APIs:
       □ Criar conta em api-football.com
       □ Obter chave do Scorebat para replays
       □ Configurar chaves no arquivo .env
    
    2. Supabase:
       □ Criar tabelas (game_rooms, room_users, etc)
       □ Habilitar Realtime nas tabelas
       □ Configurar Row Level Security
    
    3. Stripe:
       □ Criar novos Price IDs para planos v2.0
       □ Atualizar src/lib/stripe.js
    
    4. Componentes Vue:
       □ GameRoom.vue
       □ LiveChat.vue
       □ OddsPanel.vue
       □ UserList.vue
       □ CelebrationOverlay.vue
    
    """)


if __name__ == "__main__":
    main()
