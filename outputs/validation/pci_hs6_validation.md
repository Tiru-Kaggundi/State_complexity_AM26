# HS6 PCI validation

## 1. Method check (2024, OEC's countries and products)

Matrix: 130 countries x 4,541 products.

| compared with OEC 2024 | Pearson | Spearman | n |
|---|---|---|---|
| PCI (HS6) | 0.964 | 0.959 | 4,541 |
| ECI (countries) | 0.988 | 0.989 | 130 |

## 2. Main specification (2022-24 average)

Countries: 130 (in OEC's ranking all three years). Products: 4,673 HS6 lines with average world trade >= US$ 100 M. Eigenvalues: 1.000, 0.307, 0.217.

| compared with OEC (2022-24 mean) | Pearson | Spearman | n |
|---|---|---|---|
| PCI (HS6) | 0.991 | 0.990 | 4,584 |
| ECI (countries) | 0.997 | 0.998 | 130 |

## 3. Consistency with OEC HS4 PCI

Trade-weighted mean of our HS6 PCI within each HS4 vs OEC HS4 PCI: Pearson 0.958, Spearman 0.960, n = 1,072.

## 4. Country ECI

Top 10:

| rank | country | our ECI | OEC ECI | diversity |
|---|---|---|---|---|
| 1 | Japan | 2.10 | 2.06 | 1256 |
| 2 | Switzerland | 1.98 | 1.94 | 621 |
| 3 | Chinese Taipei | 1.92 | 1.92 | 768 |
| 4 | Germany | 1.82 | 1.80 | 1986 |
| 5 | South Korea | 1.81 | 1.79 | 893 |
| 6 | Singapore | 1.78 | 1.68 | 510 |
| 7 | United States | 1.56 | 1.56 | 1382 |
| 8 | Czechia | 1.56 | 1.54 | 1245 |
| 9 | Sweden | 1.56 | 1.54 | 1130 |
| 10 | Austria | 1.54 | 1.52 | 1448 |

Bottom 5:

| rank | country | our ECI | OEC ECI | diversity |
|---|---|---|---|---|
| 126 | Papua New Guinea | -1.73 | -1.71 | 64 |
| 127 | Liberia | -1.77 | -1.58 | 61 |
| 128 | Chad | -1.89 | -2.07 | 11 |
| 129 | Democratic Republic of the Congo | -2.03 | -1.92 | 39 |
| 130 | Guinea | -2.51 | -2.31 | 31 |

India: rank 40 of 130, ECI 0.53 (OEC 0.56).

## 5. Products

Most complex 15:

| HS6 | product | PCI | OEC PCI | ubiquity |
|---|---|---|---|---|
| 900120 | Optical elements: polarising material, sheets and plates thereof | 2.60 | 2.60 | 3 |
| 848630 | Machines and apparatus of a kind used solely or principally for the ma | 2.60 | 2.42 | 3 |
| 400241 | Rubber: synthetic, chloroprene (chlorobutadiene) rubber (CR), latex, i | 2.53 | 2.24 | 3 |
| 848610 | Machines and apparatus of a kind used solely or principally for the ma | 2.48 | 2.44 | 5 |
| 370790 | Photographic goods: chemical preparations other than sensitised emulsi | 2.23 | 1.78 | 4 |
| 846242 | Machine-tools: punching, notching or nibbling machines (excluding pres | 2.17 | 2.04 | 6 |
| 392073 | Plastics: plates, sheets, film, foil and strip (not self-adhesive), of | 2.16 | 2.31 | 4 |
| 400249 | Rubber: synthetic, chloroprene (chlorobutadiene) rubber (CR), (other t | 2.13 | 2.11 | 3 |
| 846022 | Machine-tools: grinding machines (excluding flat-surface), centreless, | 2.11 | 1.82 | 8 |
| 722591 | Steel, alloy: flat-rolled, width 600mm or more, n.e.c. in heading no.  | 2.00 | 1.76 | 7 |
| 284190 | Salts of oxometallic or peroxometallic acids: n.e.c. in heading no. 28 | 1.98 | 1.95 | 3 |
| 390450 | Vinyl chloride, other halogenated olefin polymers: vinylidene chloride | 1.97 | 1.84 | 3 |
| 903141 | Optical instruments and appliances: for inspecting semiconductor wafer | 1.96 | 1.92 | 6 |
| 845710 | Machining centres: for working metal | 1.96 | 1.95 | 7 |
| 844540 | Textile machinery: winding (including weft-winding) or reeling machine | 1.95 | 1.88 | 5 |

Least complex 15:

| HS6 | product | PCI | OEC PCI | ubiquity |
|---|---|---|---|---|
| 400122 | Rubber: technically specified natural rubber (TSNR), in primary forms  | -3.00 | -2.94 | 16 |
| 260900 | Tin ores and concentrates | -3.01 | -2.88 | 15 |
| 030572 | Fish: edible offal, fish heads, tails and maws | -3.02 | -3.11 | 34 |
| 530310 | Jute and other textile bast fibres: raw or retted, but not spun, (excl | -3.03 | -2.86 | 6 |
| 080132 | Nuts, edible: cashew nuts, fresh or dried, shelled | -3.03 | -2.93 | 20 |
| 400129 | Rubber: natural (excluding latex, technically specified natural rubber | -3.07 | -2.98 | 18 |
| 120740 | Oil seeds: sesamum seeds, whether or not broken | -3.19 | -3.22 | 29 |
| 440342 | Wood, tropical: teak, in the rough, whether or not stripped of bark or | -3.28 | -3.17 | 23 |
| 440728 | Wood, tropical: iroko, sawn or chipped lengthwise, sliced or peeled, w | -3.29 |  | 12 |
| 440349 | Wood, tropical: other than dark red meranti, light red meranti meranti | -3.33 | -3.42 | 34 |
| 071360 | Vegetables, leguminous: pigeon peas (Cajanus cajan), shelled, whether  | -3.35 | -3.38 | 11 |
| 400121 | Rubber: natural (excluding latex), in smoked sheets | -3.38 | -3.30 | 13 |
| 180100 | Cocoa beans: whole or broken, raw or roasted | -3.41 | -3.56 | 24 |
| 080131 | Nuts, edible: cashew nuts, fresh or dried, in shell | -3.92 | -4.11 | 15 |
| 180200 | Cocoa: shells, husks, skins and other cocoa waste | -4.16 | -4.09 | 7 |

Spotlight (India-relevant HS6 splits):

| HS6 | product | PCI | OEC PCI | ubiquity |
|---|---|---|---|---|
| 710210 | Diamonds, unsorted | -2.26 | -1.71 | 8 |
| 710221 | Diamonds, industrial, unworked | -2.16 | -1.77 | 16 |
| 710231 | Diamonds, non-industrial, unworked (rough) | -1.65 | -1.61 | 19 |
| 710239 | Diamonds, non-industrial, worked (cut & polished) | -0.58 | -0.40 | 15 |
| 300410 | Medicaments with penicillins | -0.12 | -0.16 | 30 |
| 300490 | Other medicaments, retail packs | 0.47 | 0.54 | 27 |
| 851713 | Smartphones | -0.18 | -0.15 | 9 |
| 851762 | Network equipment (switching/routing) | 0.52 | 0.51 | 16 |
| 271000 | Petroleum oils, not crude (BACI/OEC merge all of 2710 here) | -0.97 | -1.01 | 32 |
| 100630 | Rice, semi/wholly milled | -2.28 | -2.17 | 15 |
| 620520 | Men's cotton shirts | -1.77 | -1.74 | 28 |

## 6. Coverage of India's FY26 state exports (excluding 'Unspecified')

- HS6 code has a PCI directly: 88.4% of export value
- after mapping missing codes to their heading's 'xxxx00' code: 99.6%

Headings matched through 'xxxx00' (US$ bn):

- 271000: 48.8

Largest exports still without a PCI (US$ bn; small products below the trade cut-off):

- 610729 NIGHTSHIRTS AND PYJAMAS OF OTHR TXTL MATRLS: 0.08
- 292146 AMFETAMINE BENZFETAMINE ETC THR SALTS: 0.06
- 630240 TABLE LINEN,KNITTED OR CROCHETED: 0.05
- 293959 OTHER THEOPHYLLINE AND AMINOPHYLLINE THR DRVTVS, S: 0.05
- 120300 COPRA: 0.04
- 282741 CHLORIDE OXIDS AND CHLRIDE HYDROXDS OF COPPR: 0.04
- 291813 SALTS AND ESTERS OF TARTARIC ACID: 0.04
- 570220 FLR CVRNGS OF COCONUT FIBRES(COIR): 0.03
- 293942 PSEUDOEPHEDRINE (INN) AND ITS SALTS (ALKALOIDS OF : 0.03
- 844629 WEAVING MACINES FOR WEAVING FABRICS OF A WIDTH 30 : 0.03

Lowest coverage among states with exports above US$ 100 M:

- Jammu and Kashmir: 98.6%
- Punjab: 98.6%
- Kerala: 98.7%
- Himachal Pradesh: 99.1%
- Madhya Pradesh: 99.1%
