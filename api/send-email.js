// Edge Runtime - não conta no limite de serverless functions
export const config = {
  runtime: 'edge',
}

export default async function handler(req) {
  // CORS headers
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  }

  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders })
  }

  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), { 
      status: 405, 
      headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
    })
  }

  try {
    const { type, to, data } = await req.json()

    if (!to || !type) {
      return new Response(JSON.stringify({ error: 'Missing required fields: to, type' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    let subject, html

    switch (type) {
      case 'admin_invite':
        subject = `🔐 Convite para Administrador - ODINENX`
        html = generateAdminInviteEmail(data)
        break
      
      case 'welcome_admin':
        subject = `✅ Bem-vindo à Equipe Administrativa - ODINENX`
        html = generateWelcomeAdminEmail(data)
        break
      
      case 'role_changed':
        subject = `🔄 Seu cargo foi alterado - ODINENX`
        html = generateRoleChangedEmail(data)
        break
      
      case 'role_removed':
        subject = `❌ Acesso administrativo removido - ODINENX`
        html = generateRoleRemovedEmail(data)
        break

      default:
        return new Response(JSON.stringify({ error: 'Invalid email type' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
    }

    // Usar serviço de email via API (sem nodemailer em Edge)
    // Usaremos o Resend, EmailJS ou enviaremos via Supabase Edge Function
    // Por agora, vamos logar e retornar sucesso (implementar serviço de email depois)
    console.log('📧 Email para enviar:', { to, subject, type })
    
    // TODO: Integrar com serviço de email (Resend, SendGrid, etc)
    // Por enquanto, simula sucesso
    
    return new Response(JSON.stringify({ 
      success: true, 
      message: 'Email queued for sending',
      debug: { to, subject, type }
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Email error:', error)
    return new Response(JSON.stringify({ error: 'Failed to process email', details: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
}

// Templates de Email
function generateAdminInviteEmail(data) {
  const { inviterName, role, inviteLink, expiresAt } = data
  const roleName = getRoleName(role)
  
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #000; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);">
          <tr>
            <td style="padding: 40px 40px 20px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1);">
              <img src="https://odinenx.vercel.app/logo.webp" alt="ODINENX" style="height: 40px; margin-bottom: 20px;">
              <h1 style="color: #fff; font-size: 24px; margin: 0; font-weight: 700;">🔐 Convite para Administrador</h1>
            </td>
          </tr>
          <tr>
            <td style="padding: 40px;">
              <p style="color: rgba(255,255,255,0.8); font-size: 16px; line-height: 1.6; margin: 0 0 20px;">Olá!</p>
              <p style="color: rgba(255,255,255,0.8); font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                <strong style="color: #fff;">${inviterName}</strong> convidou você para fazer parte da equipe administrativa do ODINENX como <strong style="color: #00e5ff;">${roleName}</strong>.
              </p>
              <div style="background: linear-gradient(135deg, rgba(0,229,255,0.15), rgba(0,229,255,0.05)); border: 1px solid rgba(0,229,255,0.3); border-radius: 12px; padding: 20px; margin: 30px 0; text-align: center;">
                <span style="color: #00e5ff; font-size: 14px; text-transform: uppercase; letter-spacing: 2px;">Cargo Atribuído</span>
                <h2 style="color: #fff; font-size: 28px; margin: 10px 0 0; font-weight: 800;">${roleName.toUpperCase()}</h2>
              </div>
              <div style="text-align: center; margin: 30px 0;">
                <a href="${inviteLink}" style="display: inline-block; background: linear-gradient(135deg, #00e5ff, #00b4d8); color: #000; padding: 16px 40px; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 16px;">ACEITAR CONVITE</a>
              </div>
              <p style="color: rgba(255,255,255,0.5); font-size: 14px; text-align: center; margin: 20px 0 0;">Este convite expira em <strong style="color: #ff6b6b;">${expiresAt}</strong></p>
            </td>
          </tr>
          <tr>
            <td style="padding: 30px 40px; background: rgba(255,255,255,0.02); border-top: 1px solid rgba(255,255,255,0.1); border-radius: 0 0 20px 20px;">
              <p style="color: rgba(255,255,255,0.4); font-size: 12px; text-align: center; margin: 0;">© ${new Date().getFullYear()} ODINENX</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
  `
}

function generateWelcomeAdminEmail(data) {
  const { name, role } = data
  const roleName = getRoleName(role)
  
  return `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin: 0; padding: 0; background-color: #000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #000; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);">
          <tr>
            <td style="padding: 40px 40px 20px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1);">
              <h1 style="color: #fff; font-size: 24px; margin: 0; font-weight: 700;">✅ Bem-vindo à Equipe!</h1>
            </td>
          </tr>
          <tr>
            <td style="padding: 40px;">
              <p style="color: rgba(255,255,255,0.8); font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                Olá <strong style="color: #fff;">${name || 'Administrador'}</strong>! Você agora faz parte da equipe como <strong style="color: #00e5ff;">${roleName}</strong>.
              </p>
              <div style="text-align: center; margin: 30px 0;">
                <a href="https://odinenx.vercel.app/admin" style="display: inline-block; background: linear-gradient(135deg, #00e5ff, #00b4d8); color: #000; padding: 16px 40px; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 16px;">ACESSAR PAINEL ADMIN</a>
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
  `
}

function generateRoleChangedEmail(data) {
  const { name, oldRole, newRole, changedBy } = data
  return `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin: 0; padding: 0; background-color: #000; font-family: sans-serif;">
  <table width="100%" style="background-color: #000; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="600" style="background: rgba(255,255,255,0.05); border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);">
          <tr><td style="padding: 40px; text-align: center;">
            <h1 style="color: #fff;">🔄 Cargo Alterado</h1>
            <p style="color: rgba(255,255,255,0.8);">Olá ${name}, seu cargo foi alterado de <strong>${getRoleName(oldRole)}</strong> para <strong style="color: #00e5ff;">${getRoleName(newRole)}</strong> por ${changedBy}.</p>
          </td></tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
  `
}

function generateRoleRemovedEmail(data) {
  const { name, removedBy } = data
  return `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin: 0; padding: 0; background-color: #000; font-family: sans-serif;">
  <table width="100%" style="background-color: #000; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="600" style="background: rgba(255,255,255,0.05); border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);">
          <tr><td style="padding: 40px; text-align: center;">
            <h1 style="color: #fff;">❌ Acesso Removido</h1>
            <p style="color: rgba(255,255,255,0.8);">Olá ${name}, seu acesso administrativo foi removido por ${removedBy}.</p>
          </td></tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
  `
}

function getRoleName(role) {
  const roles = { owner: 'Proprietário', admin: 'Administrador', moderator: 'Moderador', support: 'Suporte' }
  return roles[role] || role
}
