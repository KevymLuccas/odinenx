-- ===========================================
-- ODINENX: Sistema de Administradores e Permissões
-- Migration: 016_admin_roles_system.sql
-- ===========================================

-- Tabela de cargos/roles de admin
CREATE TABLE IF NOT EXISTS admin_roles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'moderator', -- 'owner', 'admin', 'moderator', 'support'
    permissions JSONB DEFAULT '{}',
    invited_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de convites de admin
CREATE TABLE IF NOT EXISTS admin_invites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'moderator',
    permissions JSONB DEFAULT '{}',
    token TEXT NOT NULL UNIQUE,
    invited_by UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'accepted', 'expired', 'revoked'
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_admin_roles_user_id ON admin_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_roles_role ON admin_roles(role);
CREATE INDEX IF NOT EXISTS idx_admin_invites_email ON admin_invites(email);
CREATE INDEX IF NOT EXISTS idx_admin_invites_token ON admin_invites(token);
CREATE INDEX IF NOT EXISTS idx_admin_invites_status ON admin_invites(status);

-- RLS
ALTER TABLE admin_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_invites ENABLE ROW LEVEL SECURITY;

-- Políticas para admin_roles (somente admins podem ver/editar)
DROP POLICY IF EXISTS "Admins can view all roles" ON admin_roles;
CREATE POLICY "Admins can view all roles" ON admin_roles
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM admin_roles ar WHERE ar.user_id = auth.uid() AND ar.role IN ('owner', 'admin'))
        OR user_id = auth.uid()
    );

DROP POLICY IF EXISTS "Owners can manage roles" ON admin_roles;
CREATE POLICY "Owners can manage roles" ON admin_roles
    FOR ALL USING (
        EXISTS (SELECT 1 FROM admin_roles ar WHERE ar.user_id = auth.uid() AND ar.role = 'owner')
    );

DROP POLICY IF EXISTS "Admins can manage lower roles" ON admin_roles;
CREATE POLICY "Admins can manage lower roles" ON admin_roles
    FOR ALL USING (
        EXISTS (SELECT 1 FROM admin_roles ar WHERE ar.user_id = auth.uid() AND ar.role IN ('owner', 'admin'))
        AND role NOT IN ('owner')
    );

-- Políticas para admin_invites
DROP POLICY IF EXISTS "Admins can view invites" ON admin_invites;
CREATE POLICY "Admins can view invites" ON admin_invites
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM admin_roles ar WHERE ar.user_id = auth.uid() AND ar.role IN ('owner', 'admin'))
    );

DROP POLICY IF EXISTS "Admins can create invites" ON admin_invites;
CREATE POLICY "Admins can create invites" ON admin_invites
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM admin_roles ar WHERE ar.user_id = auth.uid() AND ar.role IN ('owner', 'admin'))
    );

DROP POLICY IF EXISTS "Admins can update invites" ON admin_invites;
CREATE POLICY "Admins can update invites" ON admin_invites
    FOR UPDATE USING (
        EXISTS (SELECT 1 FROM admin_roles ar WHERE ar.user_id = auth.uid() AND ar.role IN ('owner', 'admin'))
    );

DROP POLICY IF EXISTS "Admins can delete invites" ON admin_invites;
CREATE POLICY "Admins can delete invites" ON admin_invites
    FOR DELETE USING (
        EXISTS (SELECT 1 FROM admin_roles ar WHERE ar.user_id = auth.uid() AND ar.role IN ('owner', 'admin'))
    );

-- Função para verificar se é admin (atualizada)
CREATE OR REPLACE FUNCTION is_admin(user_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM admin_roles 
        WHERE user_id = user_uuid 
        AND role IN ('owner', 'admin', 'moderator', 'support')
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Função para obter role do admin
CREATE OR REPLACE FUNCTION get_admin_role(user_uuid UUID)
RETURNS TEXT AS $$
DECLARE
    user_role TEXT;
BEGIN
    SELECT role INTO user_role FROM admin_roles WHERE user_id = user_uuid;
    RETURN COALESCE(user_role, NULL);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Função para verificar permissão específica
CREATE OR REPLACE FUNCTION has_admin_permission(user_uuid UUID, permission_key TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    user_role TEXT;
    user_permissions JSONB;
BEGIN
    SELECT role, permissions INTO user_role, user_permissions 
    FROM admin_roles WHERE user_id = user_uuid;
    
    -- Owner tem todas as permissões
    IF user_role = 'owner' THEN RETURN TRUE; END IF;
    
    -- Verifica permissão específica
    IF user_permissions ? permission_key THEN
        RETURN (user_permissions->>permission_key)::BOOLEAN;
    END IF;
    
    -- Permissões padrão por role
    IF user_role = 'admin' THEN
        RETURN permission_key IN ('manage_users', 'manage_subscriptions', 'view_analytics', 'manage_invites');
    ELSIF user_role = 'moderator' THEN
        RETURN permission_key IN ('manage_users', 'view_analytics');
    ELSIF user_role = 'support' THEN
        RETURN permission_key IN ('view_users', 'view_analytics');
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_admin_roles_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_admin_roles_timestamp ON admin_roles;
CREATE TRIGGER update_admin_roles_timestamp
    BEFORE UPDATE ON admin_roles
    FOR EACH ROW EXECUTE FUNCTION update_admin_roles_timestamp();

-- Inserir owner inicial (seu usuário)
-- IMPORTANTE: Substitua pelo ID do seu usuário principal
INSERT INTO admin_roles (user_id, role, permissions)
SELECT id, 'owner', '{"all": true}'::jsonb
FROM auth.users 
WHERE email = 'kevymluccas64@gmail.com'
ON CONFLICT (user_id) DO UPDATE SET role = 'owner', permissions = '{"all": true}'::jsonb;

-- Também garantir que outros admins existentes na profiles virem owners
INSERT INTO admin_roles (user_id, role, permissions)
SELECT id, 'admin', '{}'::jsonb
FROM profiles
WHERE is_admin = true
AND id NOT IN (SELECT user_id FROM admin_roles)
ON CONFLICT (user_id) DO NOTHING;
