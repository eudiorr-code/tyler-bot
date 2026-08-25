import os
import io
import json
import datetime
import random
import threading
import asyncio
import requests
from PIL import Image, ImageDraw, ImageFont
from flask import Flask
import discord
from discord import app_commands
from discord.ui import View, Button, Select

# --- 1. SERVIDOR WEB FLASK (MANTÉM O RENDER ONLINE 24/7) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Tyler Bot (Tickets, Dropdown Roles, Warns & Tarefas em Tópicos) está online 24/7!"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. CONFIGURAÇÕES E IDS ---
ID_CRIADOR = 1533878158384955402
ID_DONO = 1533901644507517012
ID_MODERACAO = 1533937710228705443
ID_SUPORTE = 1533938661345726544

ID_CANAL_BOAS_VINDAS = 1541757103662833745
ID_CANAL_INTERESSES = 1541932784795385957

DROPDOWN_FILE = "dropdown_db.json"

def carregar_dropdown():
    if os.path.exists(DROPDOWN_FILE):
        try:
            with open(DROPDOWN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Se o arquivo não existir, retorna os padrões e já salva para a primeira vez
    padrao = [
        {
            "label": "Notificações de Eventos",
            "value": "role_eventos",
            "description": "Receba alertas quando saírem campeonatos e dinâmicas",
            "emoji": "🎉",
            "role_name": "🔔 Eventos"
        },
        {
            "label": "Podcast Avisos",
            "value": "role_podcast_avisos",
            "description": "Receba avisos sobre episódios e gravações",
            "emoji": "🔔",
            "role_name": "Podcast Avisos"
        }
    ]
    salvar_dropdown(padrao)
    return padrao

def salvar_dropdown(dados):
    with open(DROPDOWN_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --- 3. BANCO DE DADOS PERSISTENTE DE WARNS (JSON) ---
WARNS_FILE = "warns_db.json"

def carregar_warns():
    if os.path.exists(WARNS_FILE):
        try:
            with open(WARNS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salvar_warns(dados):
    with open(WARNS_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def adicionar_warn(user_id: int, motivo: str, mod_name: str) -> int:
    dados = carregar_warns()
    s_id = str(user_id)
    if s_id not in dados:
        dados[s_id] = []
    
    warn_entry = {
        "id": len(dados[s_id]) + 1,
        "motivo": motivo,
        "mod": mod_name,
        "data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    dados[s_id].append(warn_entry)
    salvar_warns(dados)
    return len(dados[s_id])

def remover_warn(user_id: int, warn_id: int) -> bool:
    dados = carregar_warns()
    s_id = str(user_id)
    if s_id not in dados:
        return False
    
    antigos = dados[s_id]
    novos = [w for w in antigos if w["id"] != warn_id]
    if len(antigos) == len(novos):
        return False
    
    for i, w in enumerate(novos, 1):
        w["id"] = i
    dados[s_id] = novos
    salvar_warns(dados)
    return True

def limpar_warns(user_id: int) -> bool:
    dados = carregar_warns()
    s_id = str(user_id)
    if s_id in dados:
        dados[s_id] = []
        salvar_warns(dados)
        return True
    return False

def obter_warns(user_id: int):
    dados = carregar_warns()
    return dados.get(str(user_id), [])

# --- 4. CONTADOR DE TICKETS ---
TICKET_COUNTER_FILE = "ticket_counter.txt"

def get_next_ticket_number():
    num = 1
    if os.path.exists(TICKET_COUNTER_FILE):
        try:
            with open(TICKET_COUNTER_FILE, "r") as f:
                num = int(f.read().strip()) + 1
        except Exception:
            num = 1
    with open(TICKET_COUNTER_FILE, "w") as f:
        f.write(str(num))
    return f"{num:04d}"

# --- 5. COLETÂNEA DE BOAS-VINDAS TYLER DURDEN ---
FRASES_BOAS_VINDAS_TYLER = [
    '"As coisas que você possui acabam possuindo você."',
    '"Você não é o seu emprego. Você não é quanto dinheiro você tem no banco."',
    '"É apenas depois de perder tudo que somos livres para fazer qualquer coisa."',
    '"Primeira regra do Clube da Luta: você não fala sobre o Clube da Luta."',
    '"Sem dor, sem sacrifício, nós não teríamos nada."',
    '"Esta é a sua vida e ela está acabando um minuto de cada vez."',
    '"Você não é especial. Você não é um floco de neve lindo e único."',
    '"O que você sabe sobre você mesmo se nunca entrou em uma briga?"',
    '"Nós somos os filhos do meio da história, cara. Sem propósito ou lugar."',
    '"Encontramos o Grande Depressão em nossas vidas. A Grande Depressão é a nossa vida espiritual."'
]

# --- 6. RESPOSTAS DO CHAT TYLER ---
def responder_como_tyler(pergunta: str) -> str:
    p = pergunta.lower()
    if "primeira regra" in p or "1 regra" in p or "1ª regra" in p:
        return "A primeira regra do Clube da Luta é: **você não fala sobre o Clube da Luta.**"
    if "segunda regra" in p or "2 regra" in p or "2ª regra" in p:
        return "A segunda regra do Clube da Luta é: **VOCÊ NÃO FALA SOBRE O CLUBE DA LUTA.**"
    if "terceira regra" in p or "3 regra" in p:
        return "Terceira regra: se alguém gritar 'pára!', fraquejar, ou bater no chão, a luta acabou."
    if "sabao" in p or "sabão" in p or "gordura" in p:
        return "O sabão é o critério da civilização. Com a quantidade certa de glicerina, você pode explodir praticamente tudo."
    if "quem e voce" in p or "quem é você" in p or "quem é tyler" in p or "quem e tyler" in p:
        return "Eu sou a personificação da liberdade que você tem medo de assumir. Sou o caos que coloca ordem na sua ilusão."
    if "trabalho" in p or "emprego" in p or "dinheiro" in p or "rico" in p:
        return "Você não é o seu emprego. Você não é quanto dinheiro você tem no banco. Você não é o carro que você dirige. Você não é o conteúdo da sua carteira."
    if "perder tudo" in p or "liberdade" in p:
        return "Apenas depois de perder tudo é que somos livres para fazer qualquer coisa."
    if "vida" in p or "conselho" in p or "ajuda" in p or "o que fazer" in p or "triste" in p:
        respostas_existenciais = [
            "Pare de tentar controlar tudo e apenas deixe que aconteça. Aceite o impacto.",
            "Você passa a vida inteira comprando coisas que não precisa, com dinheiro que não tem, pra impressionar pessoas de quem nem gosta. Acorda pra realidade.",
            "Sem dor, sem sacrifício, você não teria nada. O que você quer que eu faça? Sinta pena de você?",
            "Esta é a sua vida e ela está acabando um minuto de cada vez. O que você tá esperando?",
            "Não queira ser completo. Pare de tentar ser perfeito. Apenas viva sem amarras."
        ]
        return random.choice(respostas_existenciais)
    respostas_padrao = [
        "A pergunta certa não é o que eu acho. A pergunta é: por que você ainda tá preso nessa ilusão?",
        "Você tá perdendo tempo procurando respostas prontas enquanto a sua vida tá escorrendo pelos dedos.",
        "Apenas depois de perder tudo é que você vai entender o que realmente importa.",
        "Menos conversa, mais ação. O mundo não te deve nada.",
        "Pare de buscar validação de estranhos. Faça o que precisa ser feito.",
        "Isto não é um teste. É a sua realidade. Mantenha a postura e aguente o tranco."
    ]
    return random.choice(respostas_padrao)

# --- 7. VIEWS DE DROPDOWN E TICKETS ---
class RolesDropdown(Select):
    def __init__(self):
        cargos_atuais = carregar_dropdown()
        options = [
            discord.SelectOption(label=item["label"], value=item["value"], description=item["description"], emoji=item["emoji"])
            for item in cargos_atuais
        ]
        super().__init__(placeholder="Selecione os cargos e notificações que deseja...", min_values=0, max_values=len(options), options=options, custom_id="select_autoroles")

    async def callback(self, interaction: discord.Interaction):
        cargos_atuais = carregar_dropdown()
        guild = interaction.guild
        member = interaction.user
        cargos_map = {}
        for item in cargos_atuais:
            r = discord.utils.get(guild.roles, name=item["role_name"])
            if r: cargos_map[item["value"]] = r

        cargos_adicionados = []
        cargos_removidos = []
        for value, role in cargos_map.items():
            if value in self.values:
                if role not in member.roles:
                    await member.add_roles(role, reason="Auto-role dropdown")
                    cargos_adicionados.append(role.name)
            else:
                if role in member.roles:
                    await member.remove_roles(role, reason="Auto-role dropdown")
                    cargos_removidos.append(role.name)

        msg_resp = []
        if cargos_adicionados: msg_resp.append(f"✅ **Ativados:** {', '.join(cargos_adicionados)}")
        if cargos_removidos: msg_resp.append(f"❌ **Removidos:** {', '.join(cargos_removidos)}")
        if not cargos_adicionados and not cargos_removidos: msg_resp.append("ℹ️ Nenhuma alteração feita nos seus cargos.")
        await interaction.response.send_message("\n".join(msg_resp), ephemeral=True)

class RolesDropdownView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RolesDropdown())

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Encerrar Ticket", style=discord.ButtonStyle.danger, custom_id="btn_close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("⏳ Gerando histórico e encerrando o ticket...", ephemeral=False)
        channel = interaction.channel
        guild = interaction.guild
        
        messages = []
        async for msg in channel.history(limit=500, oldest_first=True):
            timestamp = msg.created_at.strftime('%d/%m/%Y %H:%M:%S')
            author = f"{msg.author.display_name} (@{msg.author.name})"
            content = msg.clean_content or "[Mídia/Anexo/Embed]"
            messages.append(f"[{timestamp}] {author}: {content}")
            
        transcript_text = f"=== HISTÓRICO DO TICKET: {channel.name.upper()} ===\nData de Encerramento: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\nEncerrado por: {interaction.user.display_name} (@{interaction.user.name})\n\n" + "\n".join(messages)
        file_data = io.BytesIO(transcript_text.encode('utf-8'))
        transcript_file = discord.File(file_data, filename=f"log-{channel.name}.txt")
        
        canal_logs = discord.utils.get(guild.channels, name="📁-ʟᴏɢs-ᴛɪᴄᴋᴇᴛs")
        if canal_logs:
            await canal_logs.send(
                content=f"📑 **LOG DE ATENDIMENTO ENCERRADO:** `{channel.name}`\n👤 **Encerrado por:** {interaction.user.mention}",
                file=transcript_file
            )
            
        try:
            file_data.seek(0)
            await interaction.user.send(
                content=f"Aqui está a cópia do atendimento `{channel.name}` que acabou de ser encerrado no servidor.",
                file=discord.File(file_data, filename=f"log-{channel.name}.txt")
            )
        except Exception:
            pass

        await discord.utils.sleep_until(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=3))
        await channel.delete(reason=f"Ticket {channel.name} encerrado por {interaction.user.name}")

class OpenTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Abrir Suporte", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="btn_open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user
        ticket_num = get_next_ticket_number()
        channel_name = f"🎫-ticket-{ticket_num}"
        cat_suporte = discord.utils.get(guild.categories, name="📣 𝑪𝒆𝒏𝒕𝒓𝒂𝒍 𝒅𝒂 𝑺𝑻𝑨𝑭𝑭 ↩") or interaction.channel.category
        
        cargo_sup = guild.get_role(ID_SUPORTE)
        cargo_mod = guild.get_role(ID_MODERACAO)
        cargo_dono = guild.get_role(ID_DONO)
        cargo_criador = guild.get_role(ID_CRIADOR)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True)
        }
        if cargo_sup: overwrites[cargo_sup] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if cargo_mod: overwrites[cargo_mod] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if cargo_dono: overwrites[cargo_dono] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if cargo_criador: overwrites[cargo_criador] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        try:
            ticket_channel = await guild.create_text_channel(name=channel_name, category=cat_suporte, overwrites=overwrites, reason=f"Ticket #{ticket_num} aberto por {user.name}")
            await interaction.response.send_message(f"✅ Seu ticket foi aberto com sucesso! Acesse aqui: <#{ticket_channel.id}>", ephemeral=True)
            msg_welcome = f"""**🎫 ATENDIMENTO PRIVADO: TICKET #{ticket_num}**
👤 **Solicitante:** {user.mention}
🛡️ **Equipe de Atendimento:** {cargo_sup.mention if cargo_sup else 'Suporte'}

Explique sua dúvida, denúncia ou problema com detalhes.
Nossa equipe irá responder em breve.

Clique abaixo para encerrar quando finalizar:"""
            await ticket_channel.send(content=msg_welcome, view=CloseTicketView())
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao criar ticket: {e}", ephemeral=True)

# --- 8. CLIENT, COMANDOS SLASH E TAREFAS EM TÓPICOS ---
class TylerClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(OpenTicketView())
        self.add_view(CloseTicketView())
        self.add_view(RolesDropdownView())
        try:
            guild_obj = discord.Object(id=1539438072700338256)
            self.tree.copy_global_to(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            print("[SYNC] Comandos sincronizados no servidor!")
        except Exception as e:
            print(f"[SYNC AVISO] {e}")
        await self.tree.sync()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = TylerClient()

def eh_staff(member: discord.Member) -> bool:
    ids_staff = {ID_CRIADOR, ID_DONO, ID_MODERACAO, ID_SUPORTE}
    for r in member.roles:
        if r.id in ids_staff or r.permissions.administrator or r.permissions.manage_guild or r.permissions.kick_members:
            return True
    return False

# NOVO COMANDO: /tarefa [titulo] [descricao]
@client.tree.command(name="tarefa", description="Cria uma nova tarefa oficial em formato de Tópico no canal atual.")
@app_commands.describe(titulo="Título da tarefa / missão", descricao="O que precisa ser feito (passos ou detalhes)")
async def slash_tarefa(interaction: discord.Interaction, titulo: str, descricao: str):
    if not eh_staff(interaction.user):
        await interaction.response.send_message("❌ Apenas membros da Staff podem criar tarefas.", ephemeral=True)
        return

    canal = interaction.channel
    # Criar mensagem base e iniciar Tópico
    msg_base = await canal.send(f"📌 **NOVA DEMANDA ABERTA:** `{titulo}`\n👤 **Criado por:** {interaction.user.mention}")
    
    try:
        thread = await msg_base.create_thread(
            name=f"📋-{titulo[:90]}",
            auto_archive_duration=1440, # 24 horas de inatividade para arquivar
            reason=f"Tarefa criada por {interaction.user.name}"
        )
        
        msg_topico = f"""**📋 PAINEL DA DEMANDA: {titulo.upper()}**
👤 **Responsável pela criação:** {interaction.user.mention}
📅 **Data de abertura:** {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

**O QUE PRECISA SER FEITO:**
{descricao}

---
💬 *Usem este tópico para conversar, debater ideias, mandar prints e alinhar o progresso.*
Reajam com **⏳** para assumir e **✅** quando estiver 100% concluída."""
        
        m_t = await thread.send(msg_topico)
        await m_t.add_reaction("⏳")
        
        await interaction.response.send_message(f"✅ Tópico de tarefa criado com sucesso: <#{thread.id}>", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao criar tópico: {e}", ephemeral=True)

# COMANDOS /warn, /warns, /unwarn, /clearwarns, /timeout, /remover_timeout
@client.tree.command(name="warn", description="Aplica uma advertência oficial a um membro.")
@app_commands.describe(membro="Membro a ser advertido", motivo="Motivo da advertência")
async def slash_warn(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    if not eh_staff(interaction.user):
        await interaction.response.send_message("❌ Apenas membros da Staff podem aplicar advertências.", ephemeral=True)
        return

    total = adicionar_warn(membro.id, motivo, interaction.user.display_name)
    msg_canal = f"""⚠️ **ADVERTÊNCIA APLICADA**
{membro.mention}, você cruzou a linha.
📝 **Motivo:** {motivo}
📊 **Histórico:** Esta é a sua **{total}ª advertência**. Mantenha a postura antes que a moderação tome medidas mais severas."""
    await interaction.response.send_message(msg_canal)

    canal_logs = discord.utils.get(interaction.guild.channels, name="📁-ʟᴏɢs-ᴍᴏᴅᴇʀᴀᴄᴀᴏ")
    if canal_logs:
        msg_log = f"""🚨 **REGISTRO DE ADVERTÊNCIA (WARN #{total})**
👤 **Infrator:** {membro.mention} (`{membro.id}`)
⚖️ **Moderador:** {interaction.user.mention}
📝 **Motivo:** {motivo}
📅 **Data:** {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
📊 **Total Acumulado:** {total} advertência(s)"""
        await canal_logs.send(msg_log)

@client.tree.command(name="warns", description="Consulta o histórico de advertências de um membro.")
@app_commands.describe(membro="Membro para consultar a ficha")
async def slash_warns(interaction: discord.Interaction, membro: discord.Member):
    if not eh_staff(interaction.user):
        await interaction.response.send_message("❌ Apenas membros da Staff podem consultar advertências.", ephemeral=True)
        return

    lista = obter_warns(membro.id)
    if not lista:
        await interaction.response.send_message(f"📋 O membro {membro.mention} possui a **ficha limpa** (0 advertências).", ephemeral=True)
        return

    txt_lista = [f"• **[Warn #{w['id']}]** - Motivo: `{w['motivo']}` | Por: `{w['mod']}` ({w['data']})" for w in lista]
    resumo = f"""📋 **FICHA DE ADVERTÊNCIAS: {membro.display_name}**
👤 **Membro:** {membro.mention} (`{membro.id}`)
📊 **Total:** {len(lista)} advertência(s)

""" + "\n".join(txt_lista)
    await interaction.response.send_message(resumo, ephemeral=True)

@client.tree.command(name="unwarn", description="Remove uma advertência específica do histórico do membro.")
@app_commands.describe(membro="Membro", id_do_warn="Número do warn a ser removido (ex: 1, 2)")
async def slash_unwarn(interaction: discord.Interaction, membro: discord.Member, id_do_warn: int):
    if not eh_staff(interaction.user):
        await interaction.response.send_message("❌ Apenas a Staff pode remover advertências.", ephemeral=True)
        return

    sucesso = remover_warn(membro.id, id_do_warn)
    if sucesso:
        await interaction.response.send_message(f"✅ O **Warn #{id_do_warn}** de {membro.mention} foi removido com sucesso.", ephemeral=True)
        canal_logs = discord.utils.get(interaction.guild.channels, name="📁-ʟᴏɢs-ᴍᴏᴅᴇʀᴀᴄᴀᴏ")
        if canal_logs:
            await canal_logs.send(f"🗑️ **WARN REMOVIDO:** Warn #{id_do_warn} de {membro.mention} foi cancelado por {interaction.user.mention}.")
    else:
        await interaction.response.send_message(f"❌ Não foi encontrado nenhum Warn com o ID #{id_do_warn} para este membro.", ephemeral=True)

@client.tree.command(name="clearwarns", description="Zera todas as advertências do membro (Ficha Limpa).")
@app_commands.describe(membro="Membro que terá o histórico zerado")
async def slash_clearwarns(interaction: discord.Interaction, membro: discord.Member):
    ids_altos = {ID_CRIADOR, ID_DONO, ID_MODERACAO}
    tem_permissao = any(r.id in ids_altos for r in interaction.user.roles) or interaction.user.guild_permissions.administrator
    if not tem_permissao:
        await interaction.response.send_message("❌ Apenas a Moderação ou Donos podem zerar a ficha completa de um membro.", ephemeral=True)
        return

    limpar_warns(membro.id)
    await interaction.response.send_message(f"🧹 A ficha de {membro.mention} foi **zerada** por {interaction.user.mention}.", ephemeral=False)
    canal_logs = discord.utils.get(interaction.guild.channels, name="📁-ʟᴏɢs-ᴍᴏᴅᴇʀᴀᴄᴀᴏ")
    if canal_logs:
        await canal_logs.send(f"🧹 **FICHA ZERADA:** Todas as advertências de {membro.mention} foram limpas por {interaction.user.mention}.")

@client.tree.command(name="timeout", description="Aplica castigo (silenciamento) temporário a um membro.")
@app_commands.describe(membro="Membro", minutos="Duração em minutos", motivo="Motivo do castigo")
async def slash_timeout(interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: str):
    if not eh_staff(interaction.user):
        await interaction.response.send_message("❌ Apenas membros da Staff podem aplicar timeout.", ephemeral=True)
        return
    try:
        duracao = datetime.timedelta(minutes=minutos)
        await membro.timeout(duracao, reason=f"Por {interaction.user.display_name}: {motivo}")
        await interaction.response.send_message(f"🤐 {membro.mention} foi colocado em **castigo por {minutos} minuto(s)**.\n📝 **Motivo:** {motivo}")
        canal_logs = discord.utils.get(interaction.guild.channels, name="📁-ʟᴏɢs-ᴍᴏᴅᴇʀᴀᴄᴀᴏ")
        if canal_logs:
            await canal_logs.send(f"🤐 **TIMEOUT APLICADO:** {membro.mention} | Duração: `{minutos} min` | Motivo: `{motivo}` | Por: {interaction.user.mention}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao aplicar timeout: {e}", ephemeral=True)

@client.tree.command(name="remover_timeout", description="Remove o castigo de um membro.")
@app_commands.describe(membro="Membro para remover o castigo")
async def slash_rem_timeout(interaction: discord.Interaction, membro: discord.Member):
    if not eh_staff(interaction.user):
        await interaction.response.send_message("❌ Apenas membros da Staff podem remover timeout.", ephemeral=True)
        return
    try:
        await membro.timeout(None, reason=f"Removido por {interaction.user.display_name}")
        await interaction.response.send_message(f"🔊 O castigo de {membro.mention} foi **removido**.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

@client.tree.command(name="ban", description="Bane permanentemente um usuário (funciona mesmo se ele já saiu do servidor).")
@app_commands.describe(usuario="Usuário a ser banido (pode colar o ID se ele já saiu)", motivo="Motivo do banimento")
async def slash_ban(interaction: discord.Interaction, usuario: discord.User, motivo: str):
    # Apenas criador, dono, moderação ou quem tem perm nativa
    ids_altos = {ID_CRIADOR, ID_DONO, ID_MODERACAO}
    tem_permissao = any(r.id in ids_altos for r in interaction.user.roles) or interaction.user.guild_permissions.ban_members
    if not tem_permissao:
        await interaction.response.send_message("❌ Apenas membros da Moderação, Donos ou Criador podem usar o comando de banimento.", ephemeral=True)
        return
        
    # Se a pessoa ainda estiver no servidor, verifica a hierarquia para evitar abuso
    membro_no_servidor = interaction.guild.get_member(usuario.id)
    if membro_no_servidor and membro_no_servidor.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Você não pode banir um membro que possui um cargo hierarquicamente igual ou superior ao seu.", ephemeral=True)
        return
        
    try:
        try:
            # Tenta mandar DM avisando do ban
            await usuario.send(f"🔨 Você foi **banido** permanentemente do servidor **{interaction.guild.name}**.\n📝 **Motivo:** {motivo}")
        except:
            pass # Se a DM estiver fechada ou ele não compartilhar servidor, ignora
            
        # Baniu (usando interaction.guild.ban, funciona por ID)
        await interaction.guild.ban(usuario, reason=f"Banido por {interaction.user.display_name}: {motivo}")
        await interaction.response.send_message(f"🔨 O usuário {usuario.mention} foi obliterado (banido permanentemente) do servidor.\n📝 **Motivo:** {motivo}")
        
        canal_logs = discord.utils.get(interaction.guild.channels, name="📁-ʟᴏɢs-ᴍᴏᴅᴇʀᴀᴄᴀᴏ")
        if canal_logs:
            await canal_logs.send(f"🔨 **BANIMENTO EXECUTADO:** {usuario.mention} (`{usuario.id}`)\n📝 **Motivo:** `{motivo}`\n👤 **Autoridade:** {interaction.user.mention}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro crítico ao tentar banir o usuário: {e}", ephemeral=True)

@client.tree.command(name="tyler", description="Faça uma pergunta ao Tyler Durden e encare a resposta.")
@app_commands.describe(pergunta="O que você quer perguntar?")
async def slash_tyler(interaction: discord.Interaction, pergunta: str):
    resposta = responder_como_tyler(pergunta)
    await interaction.response.send_message(resposta)

@client.tree.command(name="dar_cargo_todos", description="Dá um cargo específico para TODOS os membros do servidor de uma só vez.")
@app_commands.describe(cargo="O cargo que será dado a todos os membros")
async def slash_dar_cargo_todos(interaction: discord.Interaction, cargo: discord.Role):
    if not eh_staff(interaction.user):
        await interaction.response.send_message("❌ Apenas membros da Staff podem usar este comando.", ephemeral=True)
        return
        
    if interaction.guild.me.top_role <= cargo:
        await interaction.response.send_message(f"❌ Não tenho permissão para distribuir o cargo {cargo.mention} porque ele está acima (ou igual) ao meu próprio cargo na hierarquia.", ephemeral=True)
        return

    await interaction.response.send_message(f"⏳ **Iniciando processo!** O cargo {cargo.mention} será dado a todos os membros do servidor (isso pode demorar alguns minutos para não gerar bloqueio por spam).", ephemeral=False)
    
    async def dar_cargo_loop():
        print(f"[COMANDO] Iniciando distribuição do cargo {cargo.name} para todos os membros.")
        sucesso = 0
        erros = 0
        for membro in interaction.guild.members:
            if membro.bot:
                continue
            if cargo not in membro.roles:
                try:
                    await membro.add_roles(cargo, reason=f"Comando /dar_cargo_todos usado por {interaction.user.name}")
                    sucesso += 1
                    await asyncio.sleep(1) # Pausa de 1 segundo para evitar Rate Limit (bloqueio do Discord)
                except Exception as e:
                    erros += 1
                    print(f"[ERRO] Falha ao dar cargo para {membro.name}: {e}")
                    
        print(f"[COMANDO] Distribuição concluída! Sucessos: {sucesso} | Erros: {erros}")
        try:
            await interaction.channel.send(f"✅ **Processo concluído!** O cargo `{cargo.name}` foi adicionado a **{sucesso} membros** (Erros: {erros}).")
        except:
            pass

    client.loop.create_task(dar_cargo_loop())

@client.tree.command(name="adicionar_interesse", description="Adiciona uma nova opção no menu suspenso de Interesses/Cargos.")
@app_commands.describe(cargo="O cargo do servidor que será dado", nome_no_menu="O título da opção", descricao="Descrição pequena", emoji="Opcional: O emoji do botão")
async def slash_adicionar_interesse(interaction: discord.Interaction, cargo: discord.Role, nome_no_menu: str, descricao: str, emoji: str = None):
    if not eh_staff(interaction.user):
        await interaction.response.send_message("❌ Apenas membros da Staff podem adicionar novos interesses.", ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=False)
    
    dados = carregar_dropdown()
    # Verifica limite (Discord permite max 25 em dropdowns)
    if len(dados) >= 25:
        await interaction.followup.send("❌ Limite de 25 opções no menu suspenso atingido!")
        return
        
    value_id = f"role_{cargo.id}"
    dados.append({
        "label": nome_no_menu,
        "value": value_id,
        "description": descricao,
        "emoji": emoji,
        "role_name": cargo.name
    })
    
    salvar_dropdown(dados)
    
    # Agora atualiza a mensagem original lá no canal
    canal = interaction.guild.get_channel(ID_CANAL_INTERESSES)
    if canal:
        try:
            msg = await canal.fetch_message(1541964505834328209)
            await msg.edit(view=RolesDropdownView())
            await interaction.followup.send(f"✅ Opção **{nome_no_menu}** adicionada com sucesso no painel de interesses!")
        except Exception as e:
            # Reverte a salvação caso o Discord rejeite (emoji inválido, por ex) para não quebrar o bot
            dados.pop()
            salvar_dropdown(dados)
            await interaction.followup.send(f"⚠️ Erro ao atualizar o painel (provavelmente emoji inválido). A opção foi cancelada automaticamente para evitar travamentos. Erro técnico: `{e}`")
    else:
        await interaction.followup.send("⚠️ A opção foi salva, mas não encontrei o canal para editar a mensagem.")

@client.tree.command(name="remover_interesse", description="Remove uma opção existente do menu suspenso de Interesses.")
@app_commands.describe(nome_exato="O título exato da opção (label) que você quer remover")
async def slash_remover_interesse(interaction: discord.Interaction, nome_exato: str):
    if not eh_staff(interaction.user):
        await interaction.response.send_message("❌ Apenas a Staff pode remover interesses.", ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=False)
    
    dados = carregar_dropdown()
    novo_dados = [d for d in dados if d["label"].strip().lower() != nome_exato.strip().lower()]
    
    if len(dados) == len(novo_dados):
        opcoes = ", ".join([f"'{d['label']}'" for d in dados])
        await interaction.followup.send(f"❌ Não encontrei nenhuma opção com o nome exato `{nome_exato}`.\nOpções atuais no sistema: {opcoes}")
        return
        
    salvar_dropdown(novo_dados)
    
    canal = interaction.guild.get_channel(ID_CANAL_INTERESSES)
    if canal:
        try:
            msg = await canal.fetch_message(1541964505834328209)
            await msg.edit(view=RolesDropdownView())
            await interaction.followup.send(f"🗑️ Opção **{nome_exato}** removida com sucesso do painel!")
        except Exception as e:
            await interaction.followup.send(f"⚠️ Removido do banco de dados, mas não consegui atualizar a mensagem antiga: {e}")
    else:
        await interaction.followup.send("⚠️ Removido do sistema, mas não encontrei o canal.")

@client.event
async def on_member_join(member):
    if member.bot: return
    
    # AUTO-ROLE (Pegando dinamicamente do banco de dados de Interesses)
    try:
        dados_dropdown = carregar_dropdown()
        cargos_para_dar = []
        for item in dados_dropdown:
            r = discord.utils.get(member.guild.roles, name=item["role_name"])
            if r: cargos_para_dar.append(r)
        if cargos_para_dar:
            await member.add_roles(*cargos_para_dar, reason="Auto-Role Novato")
    except Exception as e:
        print(f"[ERRO] Auto-role: {e}")
        
    canal_bv = client.get_channel(ID_CANAL_BOAS_VINDAS)
    if canal_bv:
        try:
            citacao = random.choice(FRASES_BOAS_VINDAS_TYLER)
            texto = f"Bem vindo(a) {member.mention}\n\n{citacao}"
            await canal_bv.send(texto)
        except Exception as e:
            print(f"[ERRO] Boas-vindas: {e}")

# --- EVENTOS DE AUDITORIA ---
def get_canal_auditoria(guild):
    for c in guild.channels:
        if "ᴀᴜᴅɪᴛᴏʀɪᴀ" in c.name or "auditoria" in c.name.lower():
            return c
    return None

@client.event
async def on_message_delete(message):
    if message.author.bot: return
    canal_auditoria = get_canal_auditoria(message.guild)
    if canal_auditoria:
        embed = discord.Embed(title="🗑️ Mensagem Deletada", color=discord.Color.red(), timestamp=datetime.datetime.now())
        embed.add_field(name="Autor", value=message.author.mention, inline=True)
        embed.add_field(name="Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="Conteúdo", value=message.content or "[Sem conteúdo em texto ou apagou embed/imagem]", inline=False)
        embed.set_footer(text=f"ID: {message.author.id}")
        await canal_auditoria.send(embed=embed)

@client.event
async def on_raw_message_delete(payload):
    if payload.cached_message is not None:
        return # Já foi pego pelo on_message_delete
    guild = client.get_guild(payload.guild_id)
    if not guild: return
    canal_auditoria = get_canal_auditoria(guild)
    if canal_auditoria:
        embed = discord.Embed(title="🗑️ Mensagem Antiga Deletada", color=discord.Color.dark_red(), description="Uma mensagem apagada não estava no meu cache (enviada antes de eu reiniciar).", timestamp=datetime.datetime.now())
        embed.add_field(name="Canal", value=f"<#{payload.channel_id}>", inline=True)
        embed.add_field(name="ID da Mensagem", value=payload.message_id, inline=True)
        await canal_auditoria.send(embed=embed)

@client.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content: return
    canal_auditoria = get_canal_auditoria(before.guild)
    if canal_auditoria:
        embed = discord.Embed(title="✏️ Mensagem Editada", color=discord.Color.orange(), timestamp=datetime.datetime.now())
        embed.add_field(name="Autor", value=before.author.mention, inline=True)
        embed.add_field(name="Canal", value=before.channel.mention, inline=True)
        embed.add_field(name="Antes", value=before.content[:1024] or "[Vazio]", inline=False)
        embed.add_field(name="Depois", value=after.content[:1024] or "[Vazio]", inline=False)
        embed.set_footer(text=f"ID: {before.author.id}")
        view = View()
        view.add_item(Button(label="Ir para a mensagem", url=after.jump_url))
        await canal_auditoria.send(embed=embed, view=view)

@client.event
async def on_raw_message_edit(payload):
    if payload.cached_message is not None: return
    guild = client.get_guild(payload.guild_id)
    if not guild: return
    canal_auditoria = get_canal_auditoria(guild)
    if canal_auditoria:
        embed = discord.Embed(title="✏️ Mensagem Antiga Editada", color=discord.Color.dark_orange(), description="Só consigo ler o novo conteúdo porque não estava no meu cache.", timestamp=datetime.datetime.now())
        embed.add_field(name="Canal", value=f"<#{payload.channel_id}>", inline=True)
        if "content" in payload.data:
            embed.add_field(name="Novo Conteúdo", value=payload.data["content"][:1024] or "[Vazio]", inline=False)
        await canal_auditoria.send(embed=embed)

@client.event
async def on_member_remove(member):
    canal_auditoria = get_canal_auditoria(member.guild)
    if canal_auditoria:
        embed = discord.Embed(title="🚪 Membro Saiu", color=discord.Color.dark_gray(), timestamp=datetime.datetime.now())
        embed.add_field(name="Membro", value=f"{member.display_name} ({member.mention})", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        await canal_auditoria.send(embed=embed)

@client.event
async def on_member_update(before, after):
    canal_auditoria = get_canal_auditoria(before.guild)
    if not canal_auditoria: return
    
    # Nickname changed
    if before.nick != after.nick:
        embed = discord.Embed(title="🏷️ Apelido Alterado", color=discord.Color.blue(), timestamp=datetime.datetime.now())
        embed.add_field(name="Membro", value=after.mention, inline=False)
        embed.add_field(name="Antes", value=before.nick or before.name, inline=True)
        embed.add_field(name="Depois", value=after.nick or after.name, inline=True)
        embed.set_footer(text=f"ID: {after.id}")
        await canal_auditoria.send(embed=embed)
        
    # Roles changed
    if before.roles != after.roles:
        added = [r.mention for r in after.roles if r not in before.roles]
        removed = [r.mention for r in before.roles if r not in after.roles]
        if added or removed:
            embed = discord.Embed(title="🔰 Cargos Alterados", color=discord.Color.purple(), timestamp=datetime.datetime.now())
            embed.add_field(name="Membro", value=after.mention, inline=False)
            if added:
                embed.add_field(name="Ganhos", value=", ".join(added), inline=False)
            if removed:
                embed.add_field(name="Perdidos", value=", ".join(removed), inline=False)
            embed.set_footer(text=f"ID: {after.id}")
            await canal_auditoria.send(embed=embed)
            
    # Timeout changed
    if before.timed_out_until != after.timed_out_until:
        if after.timed_out_until:
            embed = discord.Embed(title="🤐 Castigo (Timeout) Aplicado", color=discord.Color.red(), timestamp=datetime.datetime.now())
            embed.add_field(name="Membro", value=after.mention, inline=False)
            embed.add_field(name="Até", value=f"<t:{int(after.timed_out_until.timestamp())}:F>", inline=False)
            await canal_auditoria.send(embed=embed)
        else:
            embed = discord.Embed(title="🔊 Castigo (Timeout) Removido", color=discord.Color.green(), timestamp=datetime.datetime.now())
            embed.add_field(name="Membro", value=after.mention, inline=False)
            await canal_auditoria.send(embed=embed)

@client.event
async def on_message(message):
    if message.author.bot: return
    if client.user in message.mentions:
        conteudo_limpo = message.clean_content.replace(f"@{client.user.display_name}", "").replace(f"@{client.user.name}", "").strip()
        if not conteudo_limpo: conteudo_limpo = "quem e voce"
        resposta = responder_como_tyler(conteudo_limpo)
        await message.reply(resposta, mention_author=True)

@client.event
async def on_ready():
    print(f"[ONLINE] {client.user} conectado com /tarefa, Warns, Tickets e Auto-Roles!")

# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    threading.Thread(target=run_web).start()
    TOKEN = os.getenv('DISCORD_TOKEN') or os.getenv('TOKEN') or os.getenv('BOT_TOKEN')
    if TOKEN:
        client.run(TOKEN)
    else:
        print("[ERRO] DISCORD_TOKEN não encontrado.")
