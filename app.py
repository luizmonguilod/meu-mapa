from fastapi import FastAPI, Query, Request, HTTPException, status
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from pathlib import Path
import swisseph as swe
import math
import os
import secrets

BASE = Path(__file__).resolve().parent
app = FastAPI(title='Meu Mapa')

# Proteção opcional para hospedagem pública. Defina APP_PASSWORD no provedor.
# Se a variável não existir, o app funciona sem autenticação (útil para uso local).
@app.middleware('http')
async def optional_basic_auth(request: Request, call_next):
    password = os.getenv('APP_PASSWORD')
    if password and request.url.path != '/healthz':
        auth = request.headers.get('Authorization', '')
        valid = False
        if auth.startswith('Basic '):
            import base64
            try:
                userpass = base64.b64decode(auth[6:]).decode('utf-8')
                user, supplied = userpass.split(':', 1)
                expected_user = os.getenv('APP_USER', 'luiz')
                valid = secrets.compare_digest(user, expected_user) and secrets.compare_digest(supplied, password)
            except Exception:
                valid = False
        if not valid:
            return Response(status_code=status.HTTP_401_UNAUTHORIZED, headers={'WWW-Authenticate':'Basic realm="Meu Mapa"'})
    return await call_next(request)

app.mount('/static', StaticFiles(directory=BASE/'static'), name='static')

PROFILE = {
    'name': 'Luiz Augusto Pereira Monguilod',
    'birth_date': '1968-10-07',
    'birth_time': '02:30',
    'birth_place': 'Lençóis Paulista/SP, Brasil',
    'lat': -22.59861111,
    'lon': -48.80027778,
    'timezone': 'America/Sao_Paulo',
    'zodiac': 'Tropical',
    'houses': 'Placidus',
}

SIGNS = ['Áries','Touro','Gêmeos','Câncer','Leão','Virgem','Libra','Escorpião','Sagitário','Capricórnio','Aquário','Peixes']
PLANETS = {
    'Sol': swe.SUN, 'Lua': swe.MOON, 'Mercúrio': swe.MERCURY, 'Vênus': swe.VENUS,
    'Marte': swe.MARS, 'Júpiter': swe.JUPITER, 'Saturno': swe.SATURN,
    'Urano': swe.URANUS, 'Netuno': swe.NEPTUNE, 'Plutão': swe.PLUTO,
}
ASPECTS = [(0,'Conjunção',7),(60,'Sextil',4),(90,'Quadratura',6),(120,'Trígono',6),(180,'Oposição',7)]

PYTH = {
    **{c:1 for c in 'AJS'}, **{c:2 for c in 'BKT'}, **{c:3 for c in 'CLU'},
    **{c:4 for c in 'DMV'}, **{c:5 for c in 'ENW'}, **{c:6 for c in 'FOX'},
    **{c:7 for c in 'GPY'}, **{c:8 for c in 'HQZ'}, **{c:9 for c in 'IR'}
}
VOWELS = set('AEIOU')

def reduce_num(n, keep_masters=True):
    while n > 9 and not (keep_masters and n in (11,22,33)):
        n = sum(map(int, str(n)))
    return n

def life_path(d: date):
    return reduce_num(sum(map(int, d.strftime('%Y%m%d'))))

def name_numbers(name):
    chars=[c for c in name.upper() if c in PYTH]
    total=sum(PYTH[c] for c in chars)
    soul=sum(PYTH[c] for c in chars if c in VOWELS)
    personality=sum(PYTH[c] for c in chars if c not in VOWELS)
    return {'expressao': reduce_num(total), 'alma': reduce_num(soul), 'personalidade': reduce_num(personality), 'somas': {'total': total, 'vogais': soul, 'consoantes': personality}}

def local_today():
    return datetime.now(ZoneInfo(PROFILE['timezone'])).date()

def numerology_for(target: date):
    bd=date.fromisoformat(PROFILE['birth_date'])
    universal=reduce_num(sum(map(int,str(target.year))))
    py=reduce_num(reduce_num(bd.month)+reduce_num(bd.day)+universal)
    pm=reduce_num(py+target.month)
    pd=reduce_num(pm+target.day)
    n=name_numbers(PROFILE['name'])
    return {
        'life_path': life_path(bd), 'birth_day': reduce_num(bd.day),
        'attitude': reduce_num(bd.day+bd.month), **n,
        'universal_year': universal, 'personal_year': py, 'personal_month': pm, 'personal_day': pd,
    }

NUM_THEMES = {
 1:('Iniciar','autonomia, iniciativa e novos começos','impulsividade ou isolamento'),
 2:('Cooperar','parcerias, escuta e sensibilidade','indecisão ou dependência'),
 3:('Expressar','comunicação, criatividade e sociabilidade','dispersão ou superficialidade'),
 4:('Estruturar','disciplina, método e construção','rigidez ou excesso de controle'),
 5:('Explorar','mudança, liberdade e adaptação','impulsividade ou dispersão'),
 6:('Cuidar','responsabilidade, vínculos e harmonia','assumir peso demais'),
 7:('Aprofundar','estudo, reflexão e discernimento','isolamento ou excesso de análise'),
 8:('Realizar','gestão, resultado e materialização','controle ou ambição excessiva'),
 9:('Concluir','fechamento, desapego e integração','nostalgia ou dificuldade de soltar'),
 11:('Inspirar','intuição, percepção e visão','hipersensibilidade ou tensão'),
 22:('Construir grande','visão prática e impacto duradouro','sobrecarga e perfeccionismo'),
 33:('Servir','compaixão, ensino e contribuição','auto-sacrifício excessivo')
}

def jd_from_dt(dt_utc):
    h=dt_utc.hour+dt_utc.minute/60+dt_utc.second/3600
    return swe.julday(dt_utc.year,dt_utc.month,dt_utc.day,h)

def zodiac_pos(lon):
    lon%=360
    idx=int(lon//30)
    deg=lon%30
    return {'longitude': round(lon,4), 'sign': SIGNS[idx], 'degree': round(deg,2)}

def planet_positions(dt_utc):
    jd=jd_from_dt(dt_utc)
    out={}
    flags=swe.FLG_MOSEPH|swe.FLG_SPEED
    for name,p in PLANETS.items():
        xx,_=swe.calc_ut(jd,p,flags)
        out[name]={**zodiac_pos(xx[0]), 'speed': round(xx[3],4), 'retrograde': xx[3]<0}
    return jd,out

def natal_chart():
    tz=ZoneInfo(PROFILE['timezone'])
    local=datetime.combine(date.fromisoformat(PROFILE['birth_date']), time.fromisoformat(PROFILE['birth_time']), tzinfo=tz)
    utc=local.astimezone(ZoneInfo('UTC'))
    jd, planets=planet_positions(utc)
    cusps, ascmc=swe.houses_ex(jd, PROFILE['lat'], PROFILE['lon'], b'P', 0)
    houses=[zodiac_pos(c) for c in cusps]
    asc=zodiac_pos(ascmc[0]); mc=zodiac_pos(ascmc[1])
    return {'local_birth': local.isoformat(), 'utc_birth': utc.isoformat(), 'planets':planets,'houses':houses,'ascendant':asc,'midheaven':mc}

NATAL = natal_chart()

def angle_diff(a,b):
    d=abs((a-b)%360)
    return min(d,360-d)

def transit_snapshot(target: date):
    tz=ZoneInfo(PROFILE['timezone'])
    today=local_today()
    if target==today:
        local=datetime.now(tz)
    else:
        local=datetime.combine(target,time(12,0),tzinfo=tz)
    utc=local.astimezone(ZoneInfo('UTC'))
    _, trans=planet_positions(utc)
    hits=[]
    for tname,t in trans.items():
        for nname,n in NATAL['planets'].items():
            d=angle_diff(t['longitude'], n['longitude'])
            for exact,aname,orb in ASPECTS:
                delta=abs(d-exact)
                if delta<=orb:
                    score=round(orb-delta,2)
                    hits.append({'transit':tname,'aspect':aname,'natal':nname,'orb':round(delta,2),'score':score})
                    break
    hits.sort(key=lambda x:(x['orb'], -x['score']))
    return {'local_time':local.isoformat(),'planets':trans,'aspects':hits[:10]}

ASPECT_MEANING={
 'Conjunção':'intensifica e concentra o tema', 'Sextil':'abre oportunidade e cooperação',
 'Quadratura':'pede ajuste, esforço e decisão', 'Trígono':'facilita fluxo e desenvolvimento',
 'Oposição':'expõe polaridades que precisam ser equilibradas'
}

def synthesis(target: date):
    num=numerology_for(target); tr=transit_snapshot(target)
    y=NUM_THEMES.get(num['personal_year'],NUM_THEMES[reduce_num(num['personal_year'],False)])
    m=NUM_THEMES.get(num['personal_month'],NUM_THEMES[reduce_num(num['personal_month'],False)])
    d=NUM_THEMES.get(num['personal_day'],NUM_THEMES[reduce_num(num['personal_day'],False)])
    strongest=tr['aspects'][0] if tr['aspects'] else None
    astro='Sem aspecto maior muito exato no recorte diário.'
    if strongest:
        astro=f"{strongest['transit']} em {strongest['aspect'].lower()} com seu {strongest['natal']} natal: {ASPECT_MEANING[strongest['aspect']]} (orbe {strongest['orb']}°)."
    text=f"O pano de fundo do ano é {y[0].lower()} e o mês enfatiza {m[0].lower()}. Hoje, a vibração {num['personal_day']} favorece {d[1]}. {astro}"
    return {
      'headline': f"{d[0]} com consciência do ciclo",
      'summary': text,
      'potential': d[1].capitalize(),
      'attention': d[2].capitalize(),
      'action': f"Escolha uma ação concreta ligada a {d[0].lower()} sem perder de vista o tema do ano: {y[0].lower()}.",
      'question': f"O que posso {d[0].lower()} hoje para avançar de forma coerente com este ciclo?"
    }

def forecast(target: date):
    num=numerology_for(target)
    # key dates in selected month: master personal days or day numbers matching month/year vibration
    keys=[]
    import calendar
    days=calendar.monthrange(target.year,target.month)[1]
    for dd in range(1,days+1):
        x=numerology_for(date(target.year,target.month,dd))['personal_day']
        if x in (11,22,33) or x==num['personal_month'] or x==num['personal_year']:
            keys.append({'date':f'{target.year:04d}-{target.month:02d}-{dd:02d}','number':x,'theme':NUM_THEMES.get(x,NUM_THEMES[reduce_num(x,False)])[0]})
    return {'year':num['personal_year'],'month':num['personal_month'],'key_dates':keys[:12]}

@app.get('/')
def root():
    return FileResponse(BASE/'static'/'index.html')

@app.get('/api/profile')
def profile():
    return {**PROFILE,'natal':NATAL,'numbers':numerology_for(local_today())}

@app.get('/api/day')
def day_analysis(d: str = Query(default=None)):
    target=date.fromisoformat(d) if d else local_today()
    return {'date':target.isoformat(),'numerology':numerology_for(target),'transits':transit_snapshot(target),'synthesis':synthesis(target),'forecast':forecast(target)}


@app.get('/sw.js', include_in_schema=False)
def service_worker():
    return FileResponse(BASE/'static'/'sw.js', media_type='application/javascript', headers={'Service-Worker-Allowed':'/'})

@app.get('/healthz', include_in_schema=False)
def healthz():
    return {'status':'ok'}
