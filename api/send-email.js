import nodemailer from 'nodemailer'

// Configuração SMTP Hostinger
const transporter = nodemailer.createTransport({
  host: 'smtp.hostinger.com',
  port: 465,
  secure: true,
  auth: {
    user: 'suporte@fantomstore.com.br',
    pass: '157001@Luccas'
  }
})

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const { type, to, data } = req.body

    if (!to || !type) {
      return res.status(400).json({ error: 'Missing required fields: to, type' })
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
        return res.status(400).json({ error: 'Invalid email type' })
    }

    const mailOptions = {
      from: '"ODINENX Admin" <suporte@fantomstore.com.br>',
      to,
      subject,
      html
    }

    await transporter.sendMail(mailOptions)

    return res.status(200).json({ success: true, message: 'Email sent successfully' })

  } catch (error) {
    console.error('Email error:', error)
    return res.status(500).json({ error: 'Failed to send email', details: error.message })
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
          
          <!-- Header -->
          <tr>
            <td style="padding: 40px 40px 20px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1);">
              <img src="https://odinenx.vercel.app/logo.webp" alt="ODINENX" style="height: 40px; margin-bottom: 20px;">
              <h1 style="color: #fff; font-size: 24px; margin: 0; font-weight: 700;">
                🔐 Convite para Administrador
              </h1>
            </td>
          </tr>
          
          <!-- Body -->
          <tr>
            <td style="padding: 40px;">
              <p style="color: rgba(255,255,255,0.8); font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                Olá!
              </p>
              <p style="color: rgba(255,255,255,0.8); font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                <strong style="color: #fff;">${inviterName}</strong> convidou você para fazer parte da equipe administrativa do ODINENX como <strong style="color: #00e5ff;">${roleName}</strong>.
              </p>
              
              <!-- Role Badge -->
              <div style="background: linear-gradient(135deg, rgba(0,229,255,0.15), rgba(0,229,255,0.05)); border: 1px solid rgba(0,229,255,0.3); border-radius: 12px; padding: 20px; margin: 30px 0; text-align: center;">
                <span style="color: #00e5ff; font-size: 14px; text-transform: uppercase; letter-spacing: 2px;">Cargo Atribuído</span>
                <h2 style="color: #fff; font-size: 28px; margin: 10px 0 0; font-weight: 800;">${roleName.toUpperCase()}</h2>
              </div>
              
              <!-- CTA Button -->
              <div style="text-align: center; margin: 30px 0;">
                <a href="${inviteLink}" style="display: inline-block; background: linear-gradient(135deg, #00e5ff, #00b4d8); color: #000; padding: 16px 40px; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 16px;">
                  ACEITAR CONVITE
                </a>
              </div>
              
              <p style="color: rgba(255,255,255,0.5); font-size: 14px; text-align: center; margin: 20px 0 0;">
                Este convite expira em <strong style="color: #ff6b6b;">${expiresAt}</strong>
              </p>
              
              <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 30px 0;">
              
              <p style="color: rgba(255,255,255,0.5); font-size: 13px; line-height: 1.6; margin: 0;">
                Se você não solicitou este convite, pode ignorar este email. O link expirará automaticamente.
              </p>
            </td>
          </tr>
          
          <!-- Footer -->
          <tr>
            <td style="padding: 30px 40px; background: rgba(255,255,255,0.02); border-top: 1px solid rgba(255,255,255,0.1); border-radius: 0 0 20px 20px;">
              <p style="color: rgba(255,255,255,0.4); font-size: 12px; text-align: center; margin: 0;">
                © ${new Date().getFullYear()} ODINENX - Plataforma de Análises Esportivas<br>
                <a href="https://odinenx.vercel.app" style="color: #00e5ff; text-decoration: none;">odinenx.vercel.app</a>
              </p>
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
              <h1 style="color: #fff; font-size: 24px; margin: 0; font-weight: 700;">
                ✅ Bem-vindo à Equipe!
              </h1>
            </td>
          </tr>
          
          <tr>
            <td style="padding: 40px;">
              <p style="color: rgba(255,255,255,0.8); font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                Olá <strong style="color: #fff;">${name || 'Administrador'}</strong>!
              </p>
              <p style="color: rgba(255,255,255,0.8); font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                Você agora faz parte da equipe administrativa do ODINENX como <strong style="color: #00e5ff;">${roleName}</strong>.
              </p>
              
              <div style="background: linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,255,136,0.05)); border: 1px solid rgba(0,255,136,0.3); border-radius: 12px; padding: 20px; margin: 30px 0;">
                <h3 style="color: #00ff88; font-size: 16px; margin: 0 0 15px;">Suas permissões incluem:</h3>
                <ul style="color: rgba(255,255,255,0.8); font-size: 14px; line-height: 1.8; margin: 0; padding-left: 20px;">
                  ${getPermissionsList(role)}
                </ul>
              </div>
              
              <div style="text-align: center; margin: 30px 0;">
                <a href="https://odinenx.vercel.app/admin" style="display: inline-block; background: linear-gradient(135deg, #00e5ff, #00b4d8); color: #000; padding: 16px 40px; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 16px;">
                  ACESSAR PAINEL ADMIN
                </a>
              </div>
            </td>
          </tr>
          
          <tr>
            <td style="padding: 30px 40px; background: rgba(255,255,255,0.02); border-top: 1px solid rgba(255,255,255,0.1); border-radius: 0 0 20px 20px;">
              <p style="color: rgba(255,255,255,0.4); font-size: 12px; text-align: center; margin: 0;">
                © ${new Date().getFullYear()} ODINENX - Plataforma de Análises Esportivas
              </p>
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
<head>
  <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 0; background-color: #000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #000; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);">
          
          <tr>
            <td style="padding: 40px 40px 20px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1);">
              <img src="https://odinenx.vercel.app/logo.webp" alt="ODINENX" style="height: 40px; margin-bottom: 20px;">
              <h1 style="color: #fff; font-size: 24px; margin: 0; font-weight: 700;">
                🔄 Cargo Alterado
              </h1>
            </td>
          </tr>
          
          <tr>
            <td style="padding: 40px;">
              <p style="color: rgba(255,255,255,0.8); font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                Olá <strong style="color: #fff;">${name || 'Administrador'}</strong>,
              </p>
              <p style="color: rgba(255,255,255,0.8); font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                Seu cargo no ODINENX foi alterado por <strong style="color: #00e5ff;">${changedBy}</strong>.
              </p>
              
              <div style="display: flex; justify-content: center; align-items: center; gap: 20px; margin: 30px 0; text-align: center;">
                <div style="background: rgba(255,107,107,0.15); border: 1px solid rgba(255,107,107,0.3); border-radius: 12px; padding: 15px 25px;">
                  <span style="color: rgba(255,255,255,0.5); font-size: 12px;">Cargo Anterior</span>
                  <p style="color: #ff6b6b; font-size: 18px; font-weight: 700; margin: 5px 0 0;">${getRoleName(oldRole)}</p>
                </div>
                <span style="color: rgba(255,255,255,0.3); font-size: 24px;">→</span>
                <div style="background: rgba(0,229,255,0.15); border: 1px solid rgba(0,229,255,0.3); border-radius: 12px; padding: 15px 25px;">
                  <span style="color: rgba(255,255,255,0.5); font-size: 12px;">Novo Cargo</span>
                  <p style="color: #00e5ff; font-size: 18px; font-weight: 700; margin: 5px 0 0;">${getRoleName(newRole)}</p>
                </div>
              </div>
              
              <div style="text-align: center; margin: 30px 0;">
                <a href="https://odinenx.vercel.app/admin" style="display: inline-block; background: linear-gradient(135deg, #00e5ff, #00b4d8); color: #000; padding: 16px 40px; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 16px;">
                  VER MINHAS PERMISSÕES
                </a>
              </div>
            </td>
          </tr>
          
          <tr>
            <td style="padding: 30px 40px; background: rgba(255,255,255,0.02); border-top: 1px solid rgba(255,255,255,0.1); border-radius: 0 0 20px 20px;">
              <p style="color: rgba(255,255,255,0.4); font-size: 12px; text-align: center; margin: 0;">
                © ${new Date().getFullYear()} ODINENX
              </p>
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

function generateRoleRemovedEmail(data) {
  const { name, removedBy } = data
  
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 0; background-color: #000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #000; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);">
          
          <tr>
            <td style="padding: 40px 40px 20px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1);">
              <img src="https://odinenx.vercel.app/logo.webp" alt="ODINENX" style="height: 40px; margin-bottom: 20px;">
              <h1 style="color: #fff; font-size: 24px; margin: 0; font-weight: 700;">
                ❌ Acesso Removido
              </h1>
            </td>
          </tr>
          
          <tr>
            <td style="padding: 40px;">
              <p style="color: rgba(255,255,255,0.8); font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                Olá <strong style="color: #fff;">${name || 'Usuário'}</strong>,
              </p>
              <p style="color: rgba(255,255,255,0.8); font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                Seu acesso administrativo ao ODINENX foi removido por <strong style="color: #ff6b6b;">${removedBy}</strong>.
              </p>
              <p style="color: rgba(255,255,255,0.6); font-size: 14px; line-height: 1.6; margin: 20px 0 0;">
                Você ainda pode usar o sistema como usuário normal. Se você acredita que isso foi um erro, entre em contato com a equipe.
              </p>
            </td>
          </tr>
          
          <tr>
            <td style="padding: 30px 40px; background: rgba(255,255,255,0.02); border-top: 1px solid rgba(255,255,255,0.1); border-radius: 0 0 20px 20px;">
              <p style="color: rgba(255,255,255,0.4); font-size: 12px; text-align: center; margin: 0;">
                © ${new Date().getFullYear()} ODINENX
              </p>
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

// Helpers
function getRoleName(role) {
  const roles = {
    owner: 'Proprietário',
    admin: 'Administrador',
    moderator: 'Moderador',
    support: 'Suporte'
  }
  return roles[role] || role
}

function getPermissionsList(role) {
  const permissions = {
    owner: [
      '<li>Gerenciar todos os administradores</li>',
      '<li>Alterar cargos e permissões</li>',
      '<li>Gerenciar usuários e assinaturas</li>',
      '<li>Visualizar todos os analytics</li>',
      '<li>Configurações do sistema</li>'
    ],
    admin: [
      '<li>Gerenciar usuários</li>',
      '<li>Gerenciar assinaturas</li>',
      '<li>Convidar novos moderadores</li>',
      '<li>Visualizar analytics</li>'
    ],
    moderator: [
      '<li>Gerenciar usuários</li>',
      '<li>Visualizar analytics</li>',
      '<li>Suporte ao cliente</li>'
    ],
    support: [
      '<li>Visualizar usuários</li>',
      '<li>Visualizar analytics básicos</li>',
      '<li>Atendimento ao cliente</li>'
    ]
  }
  return (permissions[role] || permissions.support).join('')
}
