from math import sqrt

import torch
import torch.nn as nn
import torch.nn.functional as F
from einops import rearrange

from modules.attention.base_attention import Attention
from modules.conv.base_conv import conform_conv


class conform_ffn(nn.Module):
    def __init__(self, dim, DropoutL1: float = 0.1, DropoutL2: float = 0.1):
        super().__init__()
        self.ln1 = nn.Linear(dim, dim * 4)
        self.ln2 = nn.Linear(dim * 4, dim)
        self.drop1 = nn.Dropout(DropoutL1) if DropoutL1 > 0. else nn.Identity()
        self.drop2 = nn.Dropout(DropoutL2) if DropoutL2 > 0. else nn.Identity()
        self.act = nn.SiLU()

    def forward(self, x):
        x = self.ln1(x)
        x = self.act(x)
        x = self.drop1(x)
        x = self.ln2(x)
        return self.drop2(x)


class conform_blocke(nn.Module):
    def __init__(self, dim: int, kernel_size: int = 31, conv_drop: float = 0.1, ffn_latent_drop: float = 0.1,
                 ffn_out_drop: float = 0.1, attention_drop: float = 0.1, attention_heads: int = 4,
                 attention_heads_dim: int = 64):
        super().__init__()
        self.ffn1 = conform_ffn(dim, ffn_latent_drop, ffn_out_drop)
        self.ffn2 = conform_ffn(dim, ffn_latent_drop, ffn_out_drop)
        self.att = Attention(dim, heads=attention_heads, dim_head=attention_heads_dim)
        self.attdrop = nn.Dropout(attention_drop) if attention_drop > 0. else nn.Identity()
        self.conv = conform_conv(dim, kernel_size=kernel_size,

                                 DropoutL=conv_drop, )
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)
        self.norm3 = nn.LayerNorm(dim)
        self.norm4 = nn.LayerNorm(dim)
        self.norm5 = nn.LayerNorm(dim)


    def forward(self, x, mask=None,):
        x = self.ffn1(self.norm1(x)) * 0.5 + x


        x = self.attdrop(self.att(self.norm2(x), mask=mask)) + x
        x = self.conv(self.norm3(x)) + x
        x = self.ffn2(self.norm4(x)) * 0.5 + x
        return self.norm5(x)

        # return x


class midi_conform(nn.Module):
    def __init__(self, lay: int, dim: int, indim: int, outdim: int, use_lay_skip: bool, kernel_size: int = 31,
                 conv_drop: float = 0.1,
                 ffn_latent_drop: float = 0.1,
                 ffn_out_drop: float = 0.1, attention_drop: float = 0.1, attention_heads: int = 4,
                 attention_heads_dim: int = 64):
        super().__init__()
        self.pitch_embed = nn.Linear(1, indim)
        self.inln = nn.Linear(indim, dim)
        self.outln = nn.Linear(dim, outdim)
        self.cutheard = nn.Linear(dim, 1)
        # self.cutheard = nn.Linear(dim, outdim)
        self.lay = lay
        self.use_lay_skip = use_lay_skip
        self.cf_lay = nn.ModuleList(
            [conform_blocke(dim=dim, kernel_size=kernel_size, conv_drop=conv_drop, ffn_latent_drop=ffn_latent_drop,
                            ffn_out_drop=ffn_out_drop, attention_drop=attention_drop, attention_heads=attention_heads,
                            attention_heads_dim=attention_heads_dim) for _ in range(lay)])
        if use_lay_skip:
            self.skip_lay = nn.ModuleList([nn.Sequential(nn.Linear(dim, dim), nn.SiLU()) for _ in range(lay)])
            self.lay_sc = 1 / sqrt(lay)

    def forward(self, x, pitch, mask=None):
        layskip = 0
        # torch.masked_fill()


        x = self.inln(x )
        if mask is not None:
            x = x.masked_fill(~mask.unsqueeze(-1), 0)
        for idx, i in enumerate(self.cf_lay):
            x = i(x)
            if self.use_lay_skip:
                layskip += self.skip_lay[idx](x)
            if mask is not None:
                x = x.masked_fill(~mask.unsqueeze(-1), 0)
        if self.use_lay_skip:
            layskip = layskip * self.lay_sc
            cutprp = self.cutheard(layskip)
            midiout = self.outln(x)
        else:
            cutprp = self.cutheard(x)
            midiout = self.outln(x)
        cutprp = torch.sigmoid(cutprp)
        cutprp = torch.squeeze(cutprp, -1)
        midiout = torch.sigmoid(midiout)
        return midiout, cutprp