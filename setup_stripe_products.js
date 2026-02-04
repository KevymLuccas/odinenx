/**
 * 🚀 ODINENX v2.0 - Setup Stripe Products
 * 
 * Este script cria os produtos e preços no Stripe automaticamente.
 * 
 * Como usar:
 * 1. Instale o Stripe: npm install stripe
 * 2. Execute: node setup_stripe_products.js SUA_CHAVE_STRIPE
 *    Exemplo: node setup_stripe_products.js sk_live_51xxxxx
 */

import Stripe from 'stripe';
import fs from 'fs';

// Pegar a chave do argumento ou ambiente
const stripeSecretKey = process.argv[2] || process.env.STRIPE_SECRET_KEY;

if (!stripeSecretKey) {
    console.error('❌ Erro: Chave do Stripe não fornecida!');
    console.log('\n📋 Como usar:');
    console.log('   node setup_stripe_products.js SUA_CHAVE_STRIPE');
    console.log('   Exemplo: node setup_stripe_products.js sk_live_51xxxxx');
    console.log('\n🔑 Pegue sua chave em: https://dashboard.stripe.com/apikeys');
    process.exit(1);
}

if (!stripeSecretKey.startsWith('sk_')) {
    console.error('❌ Erro: Chave inválida! Deve começar com sk_test_ ou sk_live_');
    process.exit(1);
}

const stripe = new Stripe(stripeSecretKey);

// Configuração dos planos v2.0
const plans = [
    {
        name: 'ODINENX Basic',
        description: 'Plano básico com acesso às salas ao vivo e chat',
        price: 1990, // R$ 19,90 em centavos
        features: [
            'Acesso às salas ao vivo',
            'Chat em tempo real',
            'Reações básicas (5 emojis)',
            'Histórico 7 dias'
        ],
        metadata: {
            plan_type: 'basic',
            version: 'v2.0'
        }
    },
    {
        name: 'ODINENX Pro',
        description: 'Plano profissional com GIFs, replays e badge exclusivo',
        price: 4990, // R$ 49,90 em centavos
        features: [
            'Tudo do Basic +',
            'Envio de GIFs',
            'Replay de gols',
            'Badge Pro 🔷',
            'Criar salas privadas (5)',
            'Histórico 30 dias',
            'Destaque no chat'
        ],
        metadata: {
            plan_type: 'pro',
            version: 'v2.0'
        }
    },
    {
        name: 'ODINENX Elite',
        description: 'Plano elite com todos os recursos e loja de customização',
        price: 9990, // R$ 99,90 em centavos
        features: [
            'Tudo do Pro +',
            'Badge Elite 💎',
            'Salas privadas ilimitadas',
            'Loja de customização',
            'Confetes personalizados',
            'Sons de comemoração',
            'Molduras animadas',
            'Entrada épica nas salas',
            'Suporte prioritário'
        ],
        metadata: {
            plan_type: 'elite',
            version: 'v2.0'
        }
    }
];

async function createStripeProducts() {
    console.log('🚀 Iniciando criação dos produtos Stripe...\n');
    
    const createdProducts = [];
    
    for (const plan of plans) {
        try {
            console.log(`📦 Criando produto: ${plan.name}...`);
            
            // Criar o produto
            const product = await stripe.products.create({
                name: plan.name,
                description: plan.description + ' | ' + plan.features.join(' • '),
                metadata: plan.metadata
            });
            
            console.log(`   ✅ Produto criado: ${product.id}`);
            
            // Criar o preço (assinatura mensal)
            const price = await stripe.prices.create({
                product: product.id,
                unit_amount: plan.price,
                currency: 'brl',
                recurring: {
                    interval: 'month'
                },
                metadata: plan.metadata
            });
            
            console.log(`   💰 Preço criado: ${price.id} (R$ ${(plan.price / 100).toFixed(2)}/mês)\n`);
            
            createdProducts.push({
                plan: plan.metadata.plan_type,
                productId: product.id,
                priceId: price.id,
                amount: plan.price
            });
            
        } catch (error) {
            console.error(`   ❌ Erro ao criar ${plan.name}:`, error.message);
        }
    }
    
    // Mostrar resumo
    console.log('\n' + '='.repeat(60));
    console.log('📋 RESUMO - Copie esses IDs para src/lib/stripe.js:');
    console.log('='.repeat(60) + '\n');
    
    console.log('export const STRIPE_PLANS = {');
    
    createdProducts.forEach((p, i) => {
        const comma = i < createdProducts.length - 1 ? ',' : '';
        console.log(`    ${p.plan}: {`);
        console.log(`        priceId: '${p.priceId}',`);
        console.log(`        name: 'ODINENX ${p.plan.charAt(0).toUpperCase() + p.plan.slice(1)}',`);
        console.log(`        price: ${p.amount / 100}`);
        console.log(`    }${comma}`);
    });
    
    console.log('};');
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ Configuração concluída!');
    console.log('='.repeat(60));
    
    // Salvar em arquivo JSON para referência
    const outputPath = './stripe_products_config.json';
    
    fs.writeFileSync(outputPath, JSON.stringify({
        created_at: new Date().toISOString(),
        environment: stripeSecretKey.startsWith('sk_test') ? 'test' : 'live',
        products: createdProducts
    }, null, 2));
    
    console.log(`\n💾 Configuração salva em: ${outputPath}`);
    
    return createdProducts;
}

// Executar
createStripeProducts()
    .then(() => {
        console.log('\n🎉 Pronto! Agora atualize o arquivo src/lib/stripe.js com os Price IDs acima.');
    })
    .catch(error => {
        console.error('\n❌ Erro fatal:', error.message);
        process.exit(1);
    });
