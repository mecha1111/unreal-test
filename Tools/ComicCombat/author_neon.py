"""레퍼런스 2차 제작: 시간에 따라 형태가 바뀌는 발광 폭발, 지면 페인트, 무대/하늘."""
# author_materials.py의 노드 생성 도우미를 같은 실행 컨텍스트에서 사용한다.
import unreal

def neon_shader(name,code,additive=False):
    mat=material(name)
    if additive: mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_ADDITIVE)
    uv=node(mat,unreal.MaterialExpressionTextureCoordinate,-700,-300)
    p=scalar(mat,'Progress',0,-120)
    seed=scalar(mat,'Seed',1,40)
    tint=node(mat,unreal.MaterialExpressionVectorParameter,-700,220,parameter_name='Tint',default_value=unreal.LinearColor(1,.05,.004,1))
    c=custom(mat,code,[('UV',uv,''),('Progress',p,''),('Seed',seed,''),('Tint',tint,'')])
    finish(mat,c)
    if additive:
        alpha=node(mat,unreal.MaterialExpressionComponentMask,300,170,r=False,g=False,b=False,a=True)
        MEL.connect_material_property(alpha,'',unreal.MaterialProperty.MP_OPACITY)
        MEL.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
    return mat

neon_shader('M_CC_Burst',r'''
float2 p=UV*2-1;
float a=atan2(p.y,p.x),r=length(p);
float growth=1-exp(-Progress*23);
float tongues=.36+.12*sin(a*5+Seed+Progress*11)+.09*sin(a*11-Progress*15)
    +.29*pow(abs(cos(a*4+Seed*.4)),15)+.12*pow(abs(sin(a*9)),28);
float rough=sin(p.x*57+sin(p.y*33))*sin(p.y*49+Seed)*.025;
float boundary=tongues*growth*(1-Progress*.15);
float d=r+rough-boundary;
float aa=max(fwidth(d),.004);
float coverage=1-smoothstep(-aa,aa,d);
float innerHole=smoothstep(.18,.65,Progress)*.36;
coverage*=smoothstep(innerHole-.04,innerHole+.03,r+rough*.8);
float scorch=frac(sin(dot(floor(UV*85),float2(12.9898,78.233))+Seed)*43758.5453);
coverage*=step(saturate((Progress-.48)/.52),scorch);
float rim=smoothstep(-.09,-.015,d);
float core=pow(saturate(1-r/max(boundary,.01)),3)*(1-Progress);
float band=step(.55,frac(r*16+sin(a*7+Seed)*.7-Progress*8));
float3 body=lerp(Tint.rgb*.65,Tint.rgb*3.8,band*.36+.55);
body=lerp(body,float3(1,.001,.18)*3.2,rim);
body+=float3(1,.7,.35)*core*11;
return float4(body,coverage);
''')

neon_shader('M_CC_Paint',r'''
float2 p=UV*2-1;
float a=atan2(p.y,p.x),r=length(p);
float grow=1-exp(-Progress*28);
float boundary=(.40+.12*sin(a*7+Seed)+.055*sin(a*19+Seed*2)
    +.18*pow(abs(sin(a*5+Seed)),22))*grow;
float rough=sin(p.x*71+sin(p.y*23))*sin(p.y*63)*.018;
float d=r+rough-boundary;
float coverage=1-smoothstep(-.008,.008,d);
float speck=frac(sin(dot(floor(UV*110),float2(12.9898,78.233))+Seed)*43758.5453);
coverage*=step(.06+saturate((Progress-.58)/.42)*.94,speck);
float veins=.5+.5*sin(a*17+r*45+Seed);
float3 c=lerp(Tint.rgb*.7,Tint.rgb*2.3,step(.5,veins));
c=lerp(c,float3(1,.004,.19)*2.2,smoothstep(-.10,-.02,d));
return float4(c,coverage);
''')

neon_shader('M_CC_Flash',r'''
float2 p=UV*2-1;
float r=length(p);
float core=exp(-r*r*64);
float flare=exp(-abs(p.y)*110)*exp(-abs(p.x)*2.8)
    +exp(-abs(p.x)*150)*exp(-abs(p.y)*5);
float fade=pow(saturate(1-Progress),2);
float alpha=saturate((core+flare*.6)*fade);
return float4(lerp(Tint.rgb,float3(1,.8,.55),core)*7,alpha);
''',True)

neon_shader('M_CC_Smear',r'''
float2 p=UV*2-1;
float t=saturate((p.x+1)*.5);
float width=pow(sin(t*3.14159),.65)*(.50-.20*t);
float bend=sin(t*3.14159)*.25;
float fray=sin(t*68+Seed)*.025+sin(t*147)*.012;
float d=abs(p.y-bend)-width+fray;
float head=saturate(Progress*5);
float tail=saturate((Progress-.22)/.78);
float alpha=(1-smoothstep(-.012,.012,d))*step(tail,t)*step(t,head);
float streak=step(.30,frac((p.y+sin(t*23)*.016)*19+Seed));
alpha*=lerp(.5,1,streak);
float3 c=lerp(Tint.rgb*2.5,float3(1,.002,.16)*3,smoothstep(-.08,-.01,d));
return float4(c,alpha);
''')

# 입체 전격/파편은 이미지가 아니라 실제 메시이며, 색과 발광을 공유한다.
energy=material('M_CC_Energy')
tint=node(energy,unreal.MaterialExpressionVectorParameter,-700,0,parameter_name='Tint',default_value=unreal.LinearColor(.1,.5,1,1))
gain=scalar(energy,'Energy',5,180)
mult=node(energy,unreal.MaterialExpressionMultiply,0,0)
MEL.connect_material_expressions(tint,'',mult,'A');MEL.connect_material_expressions(gain,'',mult,'B')
MEL.connect_material_property(mult,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(energy);unreal.EditorAssetLibrary.save_loaded_asset(energy,False)

sky=material('M_CC_NightSky')
sky.set_editor_property('blend_mode',unreal.BlendMode.BLEND_OPAQUE)
world=node(sky,unreal.MaterialExpressionCameraVectorWS,-700,0)
c=custom(sky,r'''
float3 dir=-normalize(World.xyz);
float horizon=exp(-abs(dir.z)*32);
float haze=exp(-abs(dir.z)*7);
float3 c=float3(.002,.001,.006)+float3(.018,.009,.045)*haze;
c+=float3(.055,.016,.12)*horizon;
return c;
''',[('World',world,'')],unreal.CustomMaterialOutputType.CMOT_FLOAT3)
MEL.connect_material_property(c,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(sky);unreal.EditorAssetLibrary.save_loaded_asset(sky,False)

# 바닥은 얕은 보라색 결, 강한 발광과 그림자를 받는 어두운 무광 재질.
stage=unreal.load_asset(ROOT+'/Materials/M_CC_ArenaFloor')
stage_color=node(stage,unreal.MaterialExpressionVectorParameter,-500,0,parameter_name='Color',default_value=unreal.LinearColor(.016,.004,.038,1))
stage_rough=scalar(stage,'Roughness',.72,170)
em=node(stage,unreal.MaterialExpressionConstant3Vector,-500,470,constant=unreal.LinearColor(.002,.0004,.006,1))
MEL.connect_material_property(em,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.recompile_material(stage);unreal.EditorAssetLibrary.save_loaded_asset(stage,False)
print('COMIC_NEON_MATERIALS_COMPLETE')
