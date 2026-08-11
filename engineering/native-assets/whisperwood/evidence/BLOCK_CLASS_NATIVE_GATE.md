# Whisperwood Block-Class Native Gate

Status: `PASS` for all ten Packet 001 block assets.

Every asset was processed from copied packet inputs through the isolated
Blockbench 5.1.6 native repair gate. Each native project now contains the
brief-required `effect` locator under the parent and transform bound by its
canonical static export. Each receipt records two save/close/reopen/export
passes, native editor warnings, input hashes, raw export hashes, and the exact
proof boundary.

| Asset | Native project SHA-256 | Geometry pass result | Warnings |
| --- | --- | --- | ---: |
| `forest_brick` | `f7a998863abd96297d3930db4c673f25c3f5b22da0a29332dd1c07e2dda7e1f5` | exact raw equality | 0 |
| `hollow_wood` | `2b1071263d87bbdc6c90ef665b0399cbe2cbf4bd37641226da458e5dca0bd10a` | exact raw equality | 0 |
| `moss_bark` | `67554e061f647da07a917345e01f4974cccd5db42c5707834cbd841328bce637` | exact raw equality | 0 |
| `stripped_whisperwood_log` | `b44e2d34eaab785f44808ad2369a35089e93b148bc4fd34607e869a585c4aece` | exact raw equality | 0 |
| `whisperwood_leaves` | `37fe1113dc3664fdc5a0c33da497bb68feb4ddcab13e29f3580c1f33b802cb28` | exact raw equality | 0 |
| `whisperwood_log` | `cf642b91c8b9af22cab08e8c89a4fedf7556f6b8ced74e2100b792de65154440` | exact raw equality | 0 |
| `whisperwood_planks` | `a3dec75f23784c73dd02b5db7719eaf37a270cb0b80e93071800fab2d0d730a1` | exact raw equality | 0 |
| `whisperwood_roots` | `7ff4e78b2fbff34cfd59f6c451bda4f86203a44e8ab049cdd31a6b8df87af739` | exact raw equality | 0 |
| `whisperwood_sapling` | `d35f8c46e70597a580d0f037e00de068361302c9993c021d1a3a6c3e81b27f45` | canonical equality; raw `0.6` versus `0.6000000000000001` | 0 |
| `whisperwood_wood` | `0d49d10da2611691e870add91640887b5f0ca774c48fafb25582594319e0a507` | exact raw equality | 0 |

The sapling result uses the receipt-bound finite-float normalization policy:
12 decimal places with maximum rounding delta `5e-13`. Raw hashes are retained,
non-finite values fail, and locator parent/position/rotation comparisons remain
exact. A `0.000001` bounds or locator drift is covered by a rejecting regression
test.

This gate proves native editable round-trip and native codec export only. It is
not Bedrock client, BDS, console, package, or shipping proof. Namespace and
shipping-path normalization remain separate engineering work.
