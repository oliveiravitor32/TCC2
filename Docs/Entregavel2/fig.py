import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
D="C:/Users/vitor/Documents/GitHub/TCC2/Docs/Entregavel2/"
def box(ax,x,y,w,h,t,fc="#ffffff",fs=8.5,bold=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.01,rounding_size=0.08",fc=fc,ec="black",lw=0.9))
    ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=fs,weight="bold" if bold else "normal",wrap=True)
def seta(ax,a,b,t=""):
    ax.annotate("",xy=b,xytext=a,arrowprops=dict(arrowstyle="-|>",lw=1))
    if t: ax.text((a[0]+b[0])/2+0.08,(a[1]+b[1])/2,t,fontsize=7.5,va="center")
# Figura 1: camadas
f,ax=plt.subplots(figsize=(10,7.6)); ax.set_xlim(0,10); ax.set_ylim(0,10.6); ax.axis("off")
cam=[("INTERFACE COM O USUÁRIO",8.6,"#eef2ff"),("INTELIGÊNCIA",6.6,"#fef9c3"),("PERSISTÊNCIA",4.6,"#e0f2fe"),("CONECTIVIDADE",2.6,"#dcfce7"),("BORDA",0.4,"#fee2e2")]
for n,y,c in cam:
    ax.add_patch(plt.Rectangle((0,y),10,1.8,fc=c,ec="#888",lw=0.6)); ax.text(0.12,y+1.62,n,fontsize=8.5,weight="bold",va="top")
box(ax,0.6,8.75,3.9,1.15,"Painel web (React + Vite, Vercel)\nmapa do bairro · monitoramento (com consumo)\ndecisões explicadas · alertas")
box(ax,5.4,8.75,3.9,1.15,"Plataforma de câmeras (emulada)\ncliente REST: evento.sh, gerador,\nbotão \"simular publicação\"")
box(ax,0.6,6.75,2.7,1.15,"Previsão XGBoost\n(próxima hora, série\nde 15 min de Zurique)")
box(ax,3.6,6.75,2.7,1.15,"Inferência Mamdani\n(base v4-volume,\n7 regras, por grupo)")
box(ax,6.6,6.75,2.9,1.15,"Verificação normativa\n(piso e taxa da NBR 5101)\n+ diagnóstico (RF11)")
box(ax,0.6,4.75,4.2,1.15,"PostgreSQL 16 (contêiner)\ncadastro, eventos, decisões,\ntelemetria, calibração, alertas")
box(ax,5.4,4.75,3.9,1.15,"API de eventos FastAPI\n(HTTPS via Caddy, X-Chave-Api)")
box(ax,0.6,2.75,4.2,1.15,"Broker Mosquitto 2\nMQTT sobre TLS, porta 8883\ncredencial e ACL por nó")
box(ax,5.4,2.75,3.9,1.15,"Internet / Wi-Fi 2,4 GHz\nVM Oracle Cloud (Docker Compose)\nDuckDNS + Let's Encrypt")
box(ax,0.6,0.55,4.2,1.15,"Nó ESP32 (BANCADA-01)\nBH1750 (I²C) · MOSFET D4184 (PWM)\nfita LED 12 V · failsafe 15 min")
box(ax,5.4,0.55,3.9,1.15,"Frota simulada (33 postes do\nJardim Helena, só demonstração)")
seta(ax,(9.75,8.75),(9.75,5.5)); ax.plot([9.75,9.3],[5.5,5.5],color="black",lw=1); ax.text(9.0,8.45,"POST /eventos",fontsize=7.5)
seta(ax,(5.4,5.3),(4.8,5.3))
seta(ax,(2.0,5.9),(2.0,6.75)); seta(ax,(3.3,7.3),(3.6,7.3)); seta(ax,(6.3,7.3),(6.6,7.3))
ax.plot([7.0,7.0,5.1,5.1],[6.75,6.3,6.3,3.3],color="black",lw=1); seta(ax,(5.1,3.3),(4.8,3.3)); ax.text(5.15,4.4,"",fontsize=7)
ax.text(5.15,6.45,"comando {nível, validade, piso, taxa}",fontsize=7.5)
seta(ax,(1.2,2.75),(1.2,1.7)); seta(ax,(3.6,1.7),(3.6,2.75)); ax.text(1.25,2.2,"comando",fontsize=7.5); ax.text(3.65,2.2,"telemetria",fontsize=7.5)

seta(ax,(0.35,8.75),(0.35,5.4)); ax.plot([0.35,0.6],[5.4,5.4],color="black",lw=1); ax.text(0.4,8.45,"GET (REST)",fontsize=7.5)
plt.tight_layout(); plt.savefig(D+"fig_arquitetura.png",dpi=200); plt.close()

# Figura 2: esquema elétrico
f,ax=plt.subplots(figsize=(10,6)); ax.set_xlim(0,10); ax.set_ylim(0,6.4); ax.axis("off")
box(ax,3.7,1.6,2.6,3.4,"ESP32 DevKit V1\n(ESP32-WROOM-32)\n38 pinos",fc="#e0f2fe",fs=9,bold=True)
box(ax,0.3,3.6,2.2,1.6,"BH1750 (GY-302)\nendereço 0x23\npull-up de I²C e\ncapacitor no próprio módulo",fc="#dcfce7")
box(ax,7.4,3.4,2.3,1.8,"Módulo MOSFET\nD4184\n(TRIG/PWM, GND,\nVIN+, VIN−, OUT+, OUT−)",fc="#fef9c3")
box(ax,7.4,0.3,2.3,1.3,"Fita LED 5050\nbranca 12 V\n3 LEDs (6 cm, 0,86 W)",fc="#fee2e2")
box(ax,3.9,0.1,2.2,0.9,"Fonte chaveada\n12 V / 2 A",fc="#f3f4f6")
box(ax,0.3,0.8,2.2,1.4,"USB do computador\nou carregador 5 V\n(alimenta o ESP32)",fc="#f3f4f6")
def fio(pts,c,t=None,tp=None):
    xs,ys=zip(*pts); ax.plot(xs,ys,color=c,lw=1.6)
    if t: ax.text(*tp,t,fontsize=7.5,color=c)
fio([(2.5,4.9),(3.7,4.9)],"#dc2626","3V3 → VCC",(2.6,5.0))
fio([(2.5,4.6),(3.7,4.6)],"black","GND → GND",(2.6,4.68))
fio([(2.5,4.3),(3.7,4.3)],"#2563eb","GPIO21 → SDA",(2.6,4.38))
fio([(2.5,4.0),(3.7,4.0)],"#16a34a","GPIO22 → SCL",(2.6,4.08))
fio([(6.3,4.6),(7.4,4.6)],"#9333ea","GPIO25 → TRIG/PWM",(6.35,4.7))
fio([(6.3,4.2),(7.4,4.2)],"black","GND → GND\n(comum)",(6.35,3.82))
fio([(6.1,0.7),(6.8,0.7),(6.8,3.6),(7.4,3.6)],"#dc2626","+12 V\n→ VIN+",(6.14,0.76))
fio([(6.1,0.4),(7.0,0.4),(7.0,3.45),(7.4,3.45)],"black","",None)
ax.text(6.14,0.14,"0 V → VIN−",fontsize=7)
fio([(8.3,3.4),(8.3,1.6)],"#dc2626","OUT+ →\n+12 V\nda fita",(7.55,2.25))
fio([(9.0,3.4),(9.0,1.6)],"black","OUT− →\n− da fita",(9.05,2.35))
fio([(2.5,1.5),(4.4,1.5),(4.4,1.6)],"#6b7280","micro-USB (5 V)",(2.6,1.58))
ax.text(5,6.15,"GND do ESP32 e 0 V da fonte de 12 V ligados no mesmo ponto (referência comum do sinal PWM)",ha="center",fontsize=8,style="italic")
plt.tight_layout(); plt.savefig(D+"fig_esquema.png",dpi=200); plt.close()
