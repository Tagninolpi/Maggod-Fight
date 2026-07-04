import random
import discord
from discord.ext import commands
from discord import app_commands
 
# ======================================================
#                  CIPHER FUNCTIONS
# ======================================================
# Burrows-Wheeler-Transform based scramble/descramble cipher.

MIN_NUMBER = 512
MAX_NUMBER = 1023

RIDDLE_LINES = [
    "🕵️ Can you solve this riddle?",
    "🔐 Somebody scrambled this on purpose... good luck!",
    "🧩 This sentence self-destructed into chaos. Care to piece it back together?",
    "🤔 Decode me if you can!",
]

REVEAL_LINES = [
    "🎉 Mystery solved!",
    "🏆 The riddle has been cracked!",
    "🔓 Case closed!",
]


def scramble(sentence: str, index, inverse=False):
    s = sentence + str(index)
    l = len(s)
    table = []
    for i in range(l):
        s2 = s[i:l] + s[0:i]
        table.append(s2)
    sorted_table = sorted(table, reverse=inverse)
    bwt = ""
    for sentence in sorted_table:
        bwt += sentence[l - 1]
    x = bwt[:len(bwt)]
    return x


def add_numbers(scrambled: str, reversed: bool):
    real_matrix = []
    matrix = []
    for letter in scrambled:
        if reversed:
            matrix.append(f"{letter}{scrambled.count(letter)-real_matrix.count(letter)-1}")
            real_matrix.append(f"{letter}")
        else:
            matrix.append(f"{letter}{real_matrix.count(letter)}")
            real_matrix.append(f"{letter}")
    return matrix


def descramble(scrambled: str, index, inverse=False):
    count_fix = add_numbers(scrambled, inverse)
    bwt_order = sorted(count_fix, reverse=inverse)
    origine = ""
    btw_o_letter = f"{str(index)}0"
    for i in range(len(count_fix)):
        index = count_fix.index(btw_o_letter)
        letter = bwt_order[index]
        origine += letter[0]
        btw_o_letter = letter
    x = origine[:len(origine) - 1]
    return x


def get_bit_list_from_number(num):
    rest = num
    bits = []
    while rest > 0:
        bit = rest.bit_length() - 1
        bits.append(bit)
        rest -= 2 ** bit
    return bits


def create_bit(number):
    bit_list = get_bit_list_from_number(number)
    if not (len(bit_list) == 0):
        result = ""
        for bit_pos in range(max(bit_list) + 1, 0, -1):
            if bit_pos - 1 in bit_list:
                result += "1"
            else:
                result += "0"
        return result
    else:
        return "0"


def get_digit(bit):
    result = 0
    for i in range(len(bit)):
        if bit[i] == "1":
            result += 2 ** (len(bit) - i - 1)
    return result


def encrypt(sentence: str, bit_key: str, encripts):
    sent = sentence
    indices = range(len(bit_key)) if encripts else range(len(bit_key) - 1, -1, -1)
    for i in indices:
        bit = bit_key[i]
        if bit == "0":
            sent = scramble(sent, i, True) if encripts else descramble(sent, i, True)
        else:
            sent = scramble(sent, i, False) if encripts else descramble(sent, i, False)
    return sent


# ======================================================
#                       MODALS
# ======================================================
class EncryptModal(discord.ui.Modal, title="Encrypt a sentence"):
    sentence = discord.ui.TextInput(
        label="Sentence (no numbers)",
        placeholder="Type the sentence you want to encrypt",
        max_length=200,
    )
    number = discord.ui.TextInput(
        label=f"Number ({MIN_NUMBER}-{MAX_NUMBER})",
        placeholder="e.g. 777",
        max_length=4,
    )

    async def on_submit(self, interaction: discord.Interaction):
        sentence_val = str(self.sentence.value)

        if len(sentence_val) == 0:
            await interaction.response.send_message("❌ You need to write something!", ephemeral=True)
            return

        if not set(sentence_val).isdisjoint(set("0123456789")):
            await interaction.response.send_message("❌ Numbers are not allowed in the sentence!", ephemeral=True)
            return

        note = ""
        try:
            bit_number = int(str(self.number.value).strip())
            if not (MIN_NUMBER <= bit_number <= MAX_NUMBER):
                raise ValueError
        except ValueError:
            bit_number = random.randrange(MIN_NUMBER, MAX_NUMBER)
            note = "⚠️ Your number was not valid, a random number was generated for you."

        bit_key = create_bit(bit_number)
        encrypted_sentence = encrypt(sentence_val, bit_key, True)

        # Private embed to the player: original sentence + key info
        private_embed = discord.Embed(
            title="🔐 Your Encryption Key",
            color=discord.Color.blurple(),
        )
        if note:
            private_embed.description = note
        private_embed.add_field(name="Original sentence", value=sentence_val, inline=False)
        private_embed.add_field(name="Number", value=str(bit_number), inline=True)
        private_embed.add_field(name="Bit key", value=f"`{bit_key}`", inline=True)
        private_embed.set_footer(text="Keep this safe — you'll need it to decrypt your sentence later.")

        await interaction.response.send_message(embed=private_embed, ephemeral=True)

        # Public embed: only the encrypted sentence + a riddle-style challenge
        public_embed = discord.Embed(
            title=random.choice(RIDDLE_LINES),
            description=f"**{interaction.user.display_name}** has encrypted a secret sentence!",
            color=discord.Color.dark_purple(),
        )
        public_embed.add_field(name="Encrypted sentence", value=f"`{encrypted_sentence}`", inline=False)
        public_embed.set_footer(text="Use /decrypt if you think you've cracked it!")

        await interaction.channel.send(embed=public_embed)


class DecryptModal(discord.ui.Modal, title="Decrypt a sentence"):
    sentence = discord.ui.TextInput(
        label="Encrypted sentence",
        placeholder="Paste the encrypted sentence here",
        max_length=200,
    )
    number = discord.ui.TextInput(
        label="Encryption number",
        placeholder="e.g. 777",
        max_length=4,
    )

    async def on_submit(self, interaction: discord.Interaction):
        encrypted_val = str(self.sentence.value)

        if len(encrypted_val) == 0:
            await interaction.response.send_message("❌ You need to write something!", ephemeral=True)
            return

        try:
            bit_number = int(str(self.number.value).strip())
            if not (MIN_NUMBER <= bit_number <= MAX_NUMBER):
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                f"❌ Invalid number. Please provide the exact encryption number "
                f"({MIN_NUMBER}-{MAX_NUMBER}) that was used to encrypt this sentence.",
                ephemeral=True,
            )
            return

        bit_key = create_bit(bit_number)
        decrypted_sentence = encrypt(encrypted_val, bit_key, False)

        result_embed = discord.Embed(
            title="🔎 Decryption Result",
            description="Here's what came out. Does it look like a real sentence?",
            color=discord.Color.blurple(),
        )
        result_embed.add_field(name="Decrypted sentence", value=decrypted_sentence, inline=False)
        result_embed.set_footer(text="Only you can see this. Want to reveal it to everyone?")

        view = RevealChoiceView(
            author_id=interaction.user.id,
            encrypted_sentence=encrypted_val,
            decrypted_sentence=decrypted_sentence,
            bit_number=bit_number,
            bit_key=bit_key,
        )

        await interaction.response.send_message(embed=result_embed, view=view, ephemeral=True)


# ======================================================
#                  REVEAL CHOICE VIEW
# ======================================================
class RevealChoiceView(discord.ui.View):
    def __init__(self, author_id, encrypted_sentence, decrypted_sentence, bit_number, bit_key):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.encrypted_sentence = encrypted_sentence
        self.decrypted_sentence = decrypted_sentence
        self.bit_number = bit_number
        self.bit_key = bit_key

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This isn't your decryption to reveal.", ephemeral=True)
            return False
        return True

    async def _disable_buttons(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Make Public", style=discord.ButtonStyle.success, emoji="📣")
    async def make_public(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._disable_buttons(interaction)

        public_embed = discord.Embed(
            title=random.choice(REVEAL_LINES),
            description=f"**{interaction.user.display_name}** cracked the code!",
            color=discord.Color.green(),
        )
        public_embed.add_field(name="Original sentence", value=self.decrypted_sentence, inline=False)
        public_embed.add_field(name="Encrypted sentence", value=f"`{self.encrypted_sentence}`", inline=False)
        public_embed.add_field(name="Number", value=str(self.bit_number), inline=True)
        public_embed.add_field(name="Bit key", value=f"`{self.bit_key}`", inline=True)

        await interaction.channel.send(embed=public_embed)
        self.stop()

    @discord.ui.button(label="Keep Private", style=discord.ButtonStyle.secondary, emoji="🤫")
    async def keep_private(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._disable_buttons(interaction)
        self.stop()


# ======================================================
#                        COG
# ======================================================
class Cipher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="encrypt", description="Encrypt a sentence")
    async def encrypt_cmd(self, interaction: discord.Interaction):
        if not interaction.channel or not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("❌ Use this in a text channel.", ephemeral=True)
            return

        await interaction.response.send_modal(EncryptModal())

    @app_commands.command(name="decrypt", description="Decrypt a sentence")
    async def decrypt_cmd(self, interaction: discord.Interaction):
        if not interaction.channel or not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("❌ Use this in a text channel.", ephemeral=True)
            return

        await interaction.response.send_modal(DecryptModal())


# ======================================================
#                       SETUP
# ======================================================
async def setup(bot):
    await bot.add_cog(Cipher(bot))