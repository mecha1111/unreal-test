#include "ComicCombatEffect.h"
#include "ExorcistFaceComponent.h"
#include "Playground.h"
#include "Components/SkeletalMeshComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "ProceduralMeshComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Math/RotationMatrix.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"
#include "HAL/IConsoleManager.h"

// 타격 크기/잔존시간은 에디터 콘솔에서도 즉시 비교할 수 있다. 이동 효과에는 적용하지 않는다.
static TAutoConsoleVariable<float> CVarComicImpactScale(TEXT("comic.VFX.ImpactScale"),1.45f,
    TEXT("Contact explosion size multiplier"),ECVF_Default);
static TAutoConsoleVariable<float> CVarComicImpactDuration(TEXT("comic.VFX.ImpactDuration"),1.6f,
    TEXT("Contact effect lifetime multiplier; initial snap is preserved by the material"),ECVF_Default);

AComicCombatEffect::AComicCombatEffect()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;
    PrimaryActorTick.TickGroup = TG_PostPhysics;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("EffectOrigin"));
    SetActorEnableCollision(false);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> P(TEXT("/Engine/BasicShapes/Plane.Plane"));
    Plane=P.Object;
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> RT(TEXT("/Game/ComicCombat/Hifi/Materials/M_HF_Ribbon.M_HF_Ribbon"));
    static ConstructorHelpers::FObjectFinder<UNiagaraSystem> NS(TEXT("/Game/ComicCombat/Hifi/NS_HF_Sparks.NS_HF_Sparks"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Movement(TEXT("/Game/ComicCombat/Materials/M_CC_Movement.M_CC_Movement"));
    RibbonMaterial=RT.Object; SparkSystem=NS.Object; MovementMaterial=Movement.Object;
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> AM(TEXT("/Game/ComicCombat/Hifi/Materials/M_HF_Animated.M_HF_Animated"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> AL(TEXT("/Game/ComicCombat/Hifi/Materials/M_HF_AnimatedLit.M_HF_AnimatedLit"));
    AnimatedMaterial=AM.Object; AnimatedLitMaterial=AL.Object;
    const TCHAR* Sheets[] = {TEXT("impact"),TEXT("shock"),TEXT("smoke"),TEXT("electric"),TEXT("ground"),TEXT("hit")};
    for (const TCHAR* Name : Sheets)
    {
        const FString Path=FCString::Strcmp(Name,TEXT("hit"))==0
            ? FString::Printf(TEXT("/Game/ComicCombat/Hifi/AnimatedTextures/T_Animated_%s.T_Animated_%s"),Name,Name)
            : FString::Printf(TEXT("/Game/ComicCombat/Hifi/CleanTextures/T_Clean_%s.T_Clean_%s"),Name,Name);
        ConstructorHelpers::FObjectFinder<UTexture2D> Texture(*Path);
        AnimatedTextures.Add(Texture.Object);
    }
    const TCHAR* Variations[] = {TEXT("jab_burst"), TEXT("cross_burst"), TEXT("rising_burst"),
        TEXT("lightning_fork"), TEXT("ground_fracture"), TEXT("arcane_punch"),
        TEXT("arcane_ultimate"), TEXT("arcane_lightning")};
    for (const TCHAR* Name : Variations)
    {
        const FString Path = FString::Printf(TEXT("/Game/ComicCombat/Hifi/CleanTextures/T_Generated_%s.T_Generated_%s"), Name, Name);
        ConstructorHelpers::FObjectFinder<UTexture2D> Texture(*Path);
        AnimatedTextures.Add(Texture.Object);
    }
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Shard(TEXT("/Game/ComicCombat/Hifi/Meshes/SM_HF_Shard.SM_HF_Shard"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> MeshMat(TEXT("/Game/ComicCombat/Hifi/Materials/M_HF_Mesh.M_HF_Mesh"));
    HifiShard=Shard.Object; HifiMeshMaterial=MeshMat.Object;
    // 이전 직렬화 필드는 호환용으로 보존하되, 더 이상 사용하지 않는 정지 그림/메시는 로드하지 않는다.
}

FComicEffectLayer& AComicCombatEffect::AddLayer(int32 Shape,const FLinearColor& Tint,
	float Delay,float Lifetime,const FVector2D& StartSize,const FVector2D& EndSize,
	bool bBillboard,UTexture2D* Texture,UMaterialInterface* OverrideMaterial)
{
	if (ActiveLayerCount == EffectLayers.Num()) EffectLayers.AddDefaulted();
	auto& L = EffectLayers[ActiveLayerCount++];
	// 컴포넌트/MID만 보존하고 이전 공격의 위치, 회전, 수명, 옵션은 모두 초기화한다.
	UStaticMeshComponent* Mesh = L.Mesh;
	UMaterialInstanceDynamic* Material = L.Material;
	L = FComicEffectLayer();
	L.Mesh = Mesh;
	L.Material = Material;
	if (!L.Mesh)
	{
		L.Mesh=NewObject<UStaticMeshComponent>(this);
		L.Mesh->SetupAttachment(RootComponent);
		L.Mesh->SetStaticMesh(Plane);
		L.Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		L.Mesh->SetCastShadow(false);
		L.Mesh->SetRenderCustomDepth(false);
		L.Mesh->SetVisibleInRayTracing(false);
		L.Mesh->bAffectDistanceFieldLighting=false;
		L.Mesh->bAffectDynamicIndirectLighting=false;
		L.Mesh->bUseAsOccluder=false;
		L.Mesh->SetReceivesDecals(false);
		L.Mesh->SetVisibility(false);
		L.Mesh->RegisterComponent();
	}
	L.Mesh->SetStaticMesh(Plane);
    const bool bContact = CachedKind==EComicEffect::Impact || CachedKind==EComicEffect::HeavyImpact || CachedKind==EComicEffect::UltimateImpact;
    L.Mesh->SetRenderCustomDepth(bContact);
    L.Mesh->SetCustomDepthStencilValue(13);
	UMaterialInterface* Mat=OverrideMaterial ? OverrideMaterial : Texture ? SpriteMaterial.Get() : ShapeMaterial.Get();
	if (!L.Material || L.Material->Parent != Mat)
	{
		L.Material=UMaterialInstanceDynamic::Create(Mat,this);
		L.Mesh->SetMaterial(0,L.Material);
	}
	else L.Material->ClearParameterValues();
	if(L.Material)
	{
		L.Material->SetVectorParameterValue(TEXT("Tint"),Tint);
		L.Material->SetScalarParameterValue(TEXT("Shape"),Shape);
		L.Material->SetScalarParameterValue(TEXT("Seed"),ActiveLayerCount*1.71f);
		if(Texture) L.Material->SetTextureParameterValue(TEXT("ImpactTexture"),Texture);
	}
	L.Delay=Delay; L.Duration=Lifetime; L.StartSize=StartSize; L.EndSize=EndSize; L.bBillboard=bBillboard;
	Duration=FMath::Max(Duration,Delay+Lifetime);
	return L;
}

void AComicCombatEffect::AddElectric(const FVector& Start,const FVector& End,const FLinearColor& Color,
	float Delay,float Lifetime,float Width,float Seed)
{
	if (ActiveElectricCount == ElectricSegments.Num()) ElectricSegments.AddDefaulted();
	auto& E = ElectricSegments[ActiveElectricCount++];
	if (!E.Mesh)
	{
		E.Mesh=NewObject<UStaticMeshComponent>(this);
		E.Mesh->SetupAttachment(RootComponent);
		E.Mesh->SetStaticMesh(CylinderMesh);
		E.Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		E.Mesh->SetCastShadow(false);
		E.Mesh->SetRenderCustomDepth(false);
		E.Mesh->SetVisibleInRayTracing(false);
		E.Mesh->bAffectDistanceFieldLighting=false;
		E.Mesh->bAffectDynamicIndirectLighting=false;
		E.Mesh->SetVisibility(false);
		E.Mesh->RegisterComponent();
		E.Material=UMaterialInstanceDynamic::Create(EnergyMaterial,this);
		E.Mesh->SetMaterial(0,E.Material);
	}
	E.Material->SetVectorParameterValue(TEXT("Tint"),Color);
	E.Start=Start; E.End=End; E.Delay=Delay; E.Duration=Lifetime; E.Width=Width; E.Seed=Seed;
	Duration=FMath::Max(Duration,Delay+Lifetime);
}

FComicEffectLayer& AComicCombatEffect::AddPainted(int32 Part, float Delay, float Lifetime,
	const FVector2D& Size, bool bBillboard, float HueOffset, float Energy)
{
	auto& Layer = AddLayer(0, FLinearColor::White, Delay, Lifetime, Size * .08f,
		Size, bBillboard, PaintedTextures[Part], PaintedMaterial);
	Layer.Pop = .10f;
	Layer.Stretch = bBillboard && Part != 20 ? .16f : 0.f;
	Layer.Drag = bBillboard ? 3.f : 0.f;
	Layer.Material->SetScalarParameterValue(TEXT("HueOffset"), HueOffset);
	Layer.Material->SetScalarParameterValue(TEXT("HueTravel"), Part == 20 ? 0.f : -.025f);
	Layer.Material->SetScalarParameterValue(TEXT("Energy"), Energy * .70f);
	const float Palette = Part == 20 ? 3.f : (Part == 10 || Part == 11 || Part == 18) ? 1.f
		: (Part == 14 || Part == 15 || Part == 16 || Part == 19) ? 2.f : 0.f;
	Layer.Material->SetScalarParameterValue(TEXT("Palette"), Palette);
	Layer.Material->SetScalarParameterValue(TEXT("Ground"), bBillboard ? 0.f : 1.f);
	Layer.Material->SetScalarParameterValue(TEXT("SurfaceRoughness"), bBillboard ? .68f : .84f);
	Layer.Material->SetScalarParameterValue(TEXT("Warp"), Part == 20 ? 0.f : bBillboard ? .010f : .004f);
	return Layer;
}

FComicEffectLayer& AComicCombatEffect::AddAnimated(int32 Part, float Delay, float Life, const FVector2D& Size, bool bBillboard)
{
    const bool Lit = Part == 2 || Part == 4;
    const bool Contact = CachedKind == EComicEffect::Impact || CachedKind == EComicEffect::HeavyImpact || CachedKind == EComicEffect::UltimateImpact;
    if (Contact) Life *= FMath::Clamp(CVarComicImpactDuration.GetValueOnGameThread(),.5f,3.f);
    auto& L = AddLayer(0,FLinearColor::White,Delay,Life,Size,Size,bBillboard,nullptr,
        Lit ? AnimatedLitMaterial.Get() : AnimatedMaterial.Get());
    // 스케일 팝 대신 독립 시트의 실제 그림 프레임이 팽창/분열/소멸을 만든다.
    L.bFastExpand = true;
    const APlaygroundCharacter* Player = Cast<APlaygroundCharacter>(GetOwner());
    const int32 HitVariation = Player ? Player->HitCount : AttackVariant;
    int32 AtlasIndex = Part;
    if (Contact && Part == 0)
    {
        if (AttackVariant == 2 || AttackVariant == 7) AtlasIndex = 8;
        else if (AttackVariant == 1) AtlasIndex = 7;
        else if (AttackVariant == 0) AtlasIndex = HitVariation % 3 == 0 ? 0 : 6;
        else AtlasIndex = HitVariation % 2 == 0 ? 7 : 0;
    }
    if (Part == 3 && (Contact || AttackVariant == 5)) AtlasIndex = 9;
    if (Part == 4 && Contact && HitVariation % 2 == 0) AtlasIndex = 10;
    // Original generated flipbooks: warm physical contact / cool hextech discharge.
    if (Contact && Part == 0 && (AttackVariant == 0 || AttackVariant == 4)) AtlasIndex = 11;
    if (CachedKind == EComicEffect::UltimateImpact && Part == 0) AtlasIndex = 12;
    if (CachedKind == EComicEffect::UltimateImpact && (Part == 1 || Part == 3)) AtlasIndex = 13;
    if (!AnimatedTextures.IsValidIndex(AtlasIndex) || !AnimatedTextures[AtlasIndex]) AtlasIndex = Part;
    L.Material->SetTextureParameterValue(TEXT("Atlas"),AnimatedTextures[AtlasIndex]);
    const int32 Rows = AtlasIndex >= 6 || Part == 0 ? 4 : Part == 1 || Part == 2 ? 3 : 2;
    L.Material->SetScalarParameterValue(TEXT("Columns"),4.f);
    L.Material->SetScalarParameterValue(TEXT("Rows"),Rows);
    L.Material->SetScalarParameterValue(TEXT("Frames"),Rows*4);
    L.Material->SetScalarParameterValue(TEXT("FastStart"),Contact && Part != 2 ? 1.f : 0.f);
    const float Hues[] = {0.f,.48f,.76f,.95f,.55f,.1f,.88f,.7f};
    L.Material->SetScalarParameterValue(TEXT("HueShift"),Part == 5 ? 0.f : Hues[FMath::Clamp(AttackVariant,0,7)]);
    L.Material->SetScalarParameterValue(TEXT("PaletteMix"),AtlasIndex >= 11 ? 0.f : Part == 2 ? .25f : 1.f);
    L.Material->SetScalarParameterValue(TEXT("Gain"),Lit ? 1.f : Part == 3 ? 1.65f : Part == 5 ? 1.f : 1.3f);
    return L;
}

void AComicCombatEffect::Initialize(EComicEffect Kind, const FVector& Direction, int32 Variant, bool bRetain)
{
	check(!bActive);
	Age = 0.f;
	Duration = 0.f;
	ActiveLayerCount = 0;
	ActiveElectricCount = 0;
	bActive = true;
	bRetained = bRetain;
	CachedKind = Kind;
	SetActorHiddenInGame(false);
	SetActorTickEnabled(true);
	Forward = Direction.GetSafeNormal();
	const FVector Right = FVector::CrossProduct(FVector::UpVector, Forward);
	const APlayerCameraManager* Camera = UGameplayStatics::GetPlayerCameraManager(this, 0);
	const FVector TowardCamera = Camera ? (Camera->GetCameraLocation() - GetActorLocation()).GetSafeNormal() : -Forward;
	if (Kind == EComicEffect::Question)
	{
		// 사용자 요청으로 빗나감 기호는 표시하지 않는다. 기존 열거형 호환성만 유지한다.
		FinishEffect();
		return;
	}
	AttackVariant = Variant;
    bFollowHand = false;
    bFollowBody = false;
	HandSamples.Reset();
	WristSamples.Reset();
    RibbonSampleTimes.Reset();
	if (TrackedRibbon) TrackedRibbon->SetVisibility(false);
	if (Kind == EComicEffect::Trail)
	{
        Duration = Variant == 5 ? .34f : .22f;
		if (!TrackedRibbon)
		{
			TrackedRibbon = NewObject<UProceduralMeshComponent>(this);
			TrackedRibbon->SetupAttachment(RootComponent);
			TrackedRibbon->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			TrackedRibbon->SetCastShadow(false);
			TrackedRibbon->SetVisibleInRayTracing(false);
			TrackedRibbon->RegisterComponent();
			TrackedRibbonMaterial = UMaterialInstanceDynamic::Create(RibbonMaterial,this);
			TrackedRibbonMaterial->SetScalarParameterValue(TEXT("Tracked"),1.f);
			TrackedRibbon->SetMaterial(0,TrackedRibbonMaterial);
		}
		TrackedRibbon->ClearAllMeshSections();
		TrackedRibbon->SetVisibility(true);
		if (ACharacter* Character=Cast<ACharacter>(GetOwner())) AddTickPrerequisiteComponent(Character->GetMesh());
	}
	else if (Kind == EComicEffect::Speed || Kind == EComicEffect::JumpTakeoff
		|| Kind == EComicEffect::AirJump || Kind == EComicEffect::Landing)
	{
		AddMovementLayers(Kind,Variant,Right);
	}
    else if (Kind == EComicEffect::Charge || Kind == EComicEffect::Recovery)
    {
        const bool Charge = Kind == EComicEffect::Charge;
        bFollowHand = Charge;
        if (Charge)
            if (ACharacter* Character = Cast<ACharacter>(GetOwner())) AddTickPrerequisiteComponent(Character->GetMesh());
        const bool Ultimate = Variant == 5;
        const float Life = Charge ? (Ultimate ? .55f : Variant == 3 ? .27f : .12f) : .22f;
        if (Charge)
        {
            const int32 Count = Ultimate ? 3 : 1;
            for (int32 I=0; I<Count; ++I)
            {
                auto& E = AddAnimated(3,I*.15f,Ultimate ? .23f : Life,FVector2D(Ultimate ? 80.f : 32.f));
                E.Offset = TowardCamera*5.f + Right*(I%2 ? -8.f : 7.f);
                E.Angle = I*113.f;
            }
        }
        else if (Ultimate || Variant == 2 || Variant == 3 || Variant == 6)
        {
            auto& Smoke = AddAnimated(2,0.f,.34f,FVector2D(35.f,45.f));
            Smoke.Offset = TowardCamera*5.f+FVector(0,0,8.f);
            Smoke.Velocity = FVector(0,0,40.f)-Forward*14.f;
        }
        Duration = FMath::Max(Duration,Life);
    }
    else if (Kind == EComicEffect::Rush)
    {
        // 발에서 떨어져 남는 먼지와 작은 전격만 사용한다. 몸을 덮는 둥근 줄기는 만들지 않는다.
        for (int32 I=0; I<2; ++I)
        {
            auto& Dust = AddAnimated(2,I*.08f,.30f,FVector2D(75.f,54.f));
            Dust.Offset = -Forward*(25.f+I*25.f)+Right*(I ? -18.f : 18.f)-FVector(0,0,55.f);
            Dust.Velocity = -Forward*100.f+FVector(0,0,35.f);
        }
        auto& E = AddAnimated(3,0.f,.20f,FVector2D(65.f,40.f));
        E.Offset = Forward*25.f+FVector(0,0,20.f);
    }

	else AddHifiImpact(Kind,Variant,TowardCamera);
	Tick(0.f);
}

void AComicCombatEffect::FinishEffect()
{
	bActive = false;
	SetActorTickEnabled(false);
	SetActorHiddenInGame(true);
	for (auto& Layer : EffectLayers) Layer.Mesh->SetVisibility(false);
	for (auto& Segment : ElectricSegments) Segment.Mesh->SetVisibility(false);
	if (TrackedRibbon) TrackedRibbon->SetVisibility(false);
	if (ImpactSparks) ImpactSparks->DeactivateImmediate();
	if (!bRetained) Destroy();
}

// 발밑의 끊어진 곡선과 먼지를 개별 수명으로 배치한다. 이동 방향은 스폰 시 고정한다.
void AComicCombatEffect::AddMovementLayers(EComicEffect Kind, int32 Variant, const FVector& Right)
{
	const bool bRunning = Kind == EComicEffect::Speed;
	const bool bAirJump = Kind == EComicEffect::AirJump;
	const bool bLanding = Kind == EComicEffect::Landing;
	const float Side = Variant % 2 ? -1.f : 1.f;
	const FLinearColor Dust(.62f, .70f, .78f);
	const FQuat GroundRotation = FRotationMatrix::MakeFromZX(FVector::UpVector, Forward).ToQuat();
	const int32 Count = bRunning ? 2 : 3;
	for (int32 I = 0; I < Count; ++I)
	{
		const float Spread = (I % 2 ? -1.f : 1.f) * Side;
		const float Size = bRunning ? 40.f - I * 10.f : bLanding ? 60.f - I * 8.f : 50.f - I * 7.f;
		auto& Curl = AddLayer(0, Dust, I * .025f, bRunning ? .17f : .26f,
			FVector2D(Size * .35f, Size * .12f), FVector2D(Size, Size * .62f), true, nullptr, MovementMaterial);
		Curl.Offset = Right * Spread * (bRunning ? 7.f : 24.f) - Forward * (I * 12.f) + FVector(0.f, 0.f, 8.f);
		Curl.Velocity = -Forward * (bRunning ? 40.f : 30.f) + Right * Spread * 45.f + FVector(0.f, 0.f, 34.f);
		Curl.Angle = Spread * (12.f + I * 14.f);
		Curl.Spin = Spread * 60.f;
		Curl.Stretch = .12f;
		Curl.Drag = 4.f;
		Curl.Pop = .02f;
		Curl.Material->SetScalarParameterValue(TEXT("Seed"), Variant * 1.37f + I * 2.1f);
	}
	// 발이 밀어낸 짧은 붓선은 지면을 따라가고 몸 뒤에 큰 흰 카드를 남기지 않는다.
	if (bRunning)
	{
		auto& Stroke = AddLayer(1, FLinearColor(.52f, .57f, .60f), 0.f, .17f,
			FVector2D(38.f, 5.f), FVector2D(85.f, 8.f), false, nullptr, MovementMaterial);
		Stroke.Offset = -Forward * 32.f + FVector(0.f, 0.f, 1.8f);
		Stroke.BaseRotation = GroundRotation;
		Stroke.Velocity = -Forward * 90.f;
		Stroke.bFastExpand = true;
	}
	else
	{
		auto& Ring = AddLayer(2, FLinearColor(.75f, .78f, .76f), 0.f, bLanding ? .28f : .24f,
			FVector2D(35.f), FVector2D(bLanding ? 140.f : bAirJump ? 105.f : 100.f), false, nullptr, MovementMaterial);
		Ring.BaseRotation = GroundRotation;
		Ring.Offset.Z = 2.f;
		Ring.bFastExpand = true;
		Ring.Material->SetScalarParameterValue(TEXT("Seed"), Variant + 3.f);
		if (!bLanding)
		{
			for (int32 I = 0; I < 2; ++I)
			{
				auto& Lift = AddLayer(1, FLinearColor(.7f, .76f, .8f), .025f, .18f,
					FVector2D(20.f, 3.f), FVector2D(80.f, 7.f), true, nullptr, MovementMaterial);
				Lift.Offset = Right * (I ? -24.f : 24.f) + FVector(0.f, 0.f, 30.f);
				Lift.Angle = 90.f + (I ? -8.f : 8.f);
				Lift.Velocity.Z = 90.f;
				Lift.bFastExpand = true;
			}
		}
	}
}

void AComicCombatEffect::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bActive) return;
    Age+=DeltaSeconds;
    if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
    {
        if (bFollowHand) SetActorLocation(UExorcistFaceComponent::StrikeLocation(Character->GetMesh(), AttackVariant));
        else if (bFollowBody) SetActorLocation(Character->GetActorLocation());
    }
    if (CachedKind == EComicEffect::Trail) UpdateTrackedRibbon();
	APlayerCameraManager* Camera=UGameplayStatics::GetPlayerCameraManager(this,0);
	for (int32 Index = 0; Index < ActiveLayerCount; ++Index)
	{
		auto& L = EffectLayers[Index];
		const float T=Age-L.Delay;
		const bool Visible=T>=0&&T<L.Duration;
		if (L.Mesh->IsVisible() != Visible) L.Mesh->SetVisibility(Visible);
		if(!Visible)continue;
		const float P=FMath::Clamp(T/L.Duration,0.f,1.f);
		const float S=FMath::Clamp(P/.36f,0.f,1.f)-1;
		const float Pop=1+(1+L.Pop*10)*S*S*S+L.Pop*10*S*S;
		const float Expand=L.bFastExpand?1-FMath::Exp(-T*L.ExpansionRate):Pop;
		const float Exit=L.bFastExpand?1.f:1-FMath::Clamp((P-.70f)/.30f,0.f,1.f)*.55f;
		FVector2D Size=FMath::Lerp(L.StartSize,L.EndSize,Expand)*Exit;
		// 초반 가로 압축/세로 신장 뒤 감쇠 진동으로 원래 모양에 정착한다.
		const float Squash=L.Stretch*FMath::Exp(-P*7.f)*FMath::Sin(P*19.f);
		Size.X*=1.f+Squash; Size.Y*=1.f-Squash*.65f;
		const float TravelTime=L.Drag>0.f ? (1.f-FMath::Exp(-L.Drag*T))/L.Drag : T;
		const FVector Loc=GetActorLocation()+L.Offset+L.Velocity*TravelTime+L.Acceleration*(.5f*T*T)
            +L.SurfaceExpansionDirection*(Size.X*.42f);
		FQuat R=L.bBillboard&&Camera?FRotationMatrix::MakeFromZY(Camera->GetCameraLocation()-Loc,FVector::UpVector).ToQuat():L.BaseRotation;
		const float W=L.Wobble*FMath::Exp(-P*9)*FMath::Cos(P*20);
		R*=FQuat(FVector::UpVector,FMath::DegreesToRadians(L.Angle+L.Spin*T+W));
		const float Sign=L.bBillboard?-1.f:1.f;
		FVector Scale(Sign*Size.X/100,Sign*Size.Y/100,L.DepthScale);
		if (L.bVolume)
		{
			Scale=FMath::Lerp(L.StartScale,L.EndScale,1.f-FMath::Exp(-T*42.f));
			R *= (L.Tumble*T).Quaternion();
		}
		L.Mesh->SetWorldTransform(FTransform(R,Loc,Scale));
		if(L.Material)L.Material->SetScalarParameterValue(TEXT("Progress"),L.bGlyph?FMath::Clamp((P-.55f)/.45f,0.f,1.f):P);
	}
	for (int32 Index = 0; Index < ActiveElectricCount; ++Index)
	{
		auto& E = ElectricSegments[Index];
		const float T=Age-E.Delay;
		const bool Visible=T>=0&&T<E.Duration;
		if (E.Mesh->IsVisible() != Visible) E.Mesh->SetVisibility(Visible);
		if(!Visible)continue;
		const float Frame=FMath::FloorToFloat(T*24);
		const float Fade=1-T/E.Duration;
		// 경로를 낮은 프레임 간격으로 재편해 전기가 불규칙하게 갈라지는 인상을 준다.
		const FVector Jitter=FVector(FMath::Sin(E.Seed+Frame*3),FMath::Cos(E.Seed*2+Frame*4),FMath::Sin(E.Seed*3+Frame))*5*Fade;
		const FVector A=GetActorLocation()+E.Start+Jitter;
		const FVector B=GetActorLocation()+E.End-Jitter*.6f;
		E.Mesh->SetWorldTransform(FTransform(FRotationMatrix::MakeFromZ(B-A).ToQuat(),
			(A+B)*.5f, FVector(E.Width*Fade/50,E.Width*Fade/50,(B-A).Size()/100)));
		E.Material->SetScalarParameterValue(TEXT("Energy"),4+Fade*5);
	}
	if(Duration>0&&Age>=Duration)FinishEffect();
}

FComicEffectLayer& AComicCombatEffect::AddVolume(UStaticMesh* Mesh,const FLinearColor& Tint,
	float Delay,float Life,const FVector& Scale,int32 Kind)
{
	auto& L=AddLayer(0,Tint,Delay,Life,FVector2D(1),FVector2D(1),false,nullptr,HifiMeshMaterial);
	L.Mesh->SetStaticMesh(Mesh);
	L.bVolume=true;
	L.StartScale=Scale*.12f;
	L.EndScale=Scale;
	L.Material->SetScalarParameterValue(TEXT("Kind"),Kind);
	return L;
}

void AComicCombatEffect::AddHifiImpact(EComicEffect Kind,int32 Variant,const FVector& TowardCamera)
{
    const bool Ultimate = Kind == EComicEffect::UltimateImpact;
    const bool Heavy = Kind == EComicEffect::HeavyImpact;
    const float SizeGain = FMath::Clamp(CVarComicImpactScale.GetValueOnGameThread(),.5f,3.f);
    // Keep the ultimate centered on contact without covering both fighters.
    const float Strength = (Ultimate ? 1.30f : Heavy ? 1.18f : .82f)*SizeGain;
    const float Start = Ultimate ? .045f : 0.f;
    const FVector Up = FVector::UpVector;
    const FVector Side = FVector::CrossProduct(Up,Forward).GetSafeNormal();
    const auto* Camera = UGameplayStatics::GetPlayerCameraManager(this,0);
    const FVector ScreenRight = Camera ? FRotationMatrix(Camera->GetCameraRotation()).GetUnitAxis(EAxis::Y) : Side;
    const float Sign = FVector::DotProduct(Forward,ScreenRight) < 0.f ? -1.f : 1.f;
    const float Angle = (Variant == 2 || Variant == 7) ? 65.f : Variant == 3 || Variant == 6 ? -38.f : 8.f;

    // 작은 접촉 균열 → 넓고 짧은 폭발 → 빈 중심과 날카로운 파편. 16장의 실제 프레임이다.
    auto& Core = AddAnimated(0,Start,Ultimate ? .37f : Heavy ? .30f : .24f,
        (Ultimate ? FVector2D(135.f,135.f) : FVector2D(155.f,85.f))*Strength);
    Core.Offset = TowardCamera*2.f;
    Core.Angle = (Variant == 2 || Variant == 7) ? 55.f : Variant == 3 || Variant == 6 ? -30.f : -8.f;

    // 방향성 충격파는 접촉점 바깥으로 넓어진다. 두 번째 파츠는 강공격에서만 반대편에 배치한다.
    const int32 Fans = 1;
    for (int32 I=0; I<Fans; ++I)
    {
        const float S = I ? -.65f : 1.f;
        auto& Fan = AddAnimated(1,Start+.012f+I*.012f,Ultimate ? .34f : .25f,
            (Ultimate ? FVector2D(170.f,170.f) : FVector2D(165.f,76.f))*Strength*(Heavy || Ultimate ? 1.f : .55f));
        Fan.Angle = (Sign*S < 0.f ? 180.f : 0.f)+Angle;
        Fan.Offset = -TowardCamera*9.f + Forward*(S*6.f) + Up*(I ? -4.f : 4.f);
        Fan.Velocity = Forward*(S*55.f)+Up*((Variant==2 || Variant==7) ? 70.f : 8.f);
    }

    if (Variant==7)
    {
    auto& Electric = AddAnimated(3,Start+.025f,.18f,FVector2D(120.f,95.f)*Strength);
    // 중심은 표면에 고정하고 작은 보조 파츠만 살짝 분리한다.
    Electric.Offset = TowardCamera*3.f+Up*7.f+Side*(Variant%2 ? -6.f : 6.f);
    Electric.Angle = Variant*57.f;
    }
    // 연기는 폭발보다 늦게 남는다. 조명을 받는 머티리얼로 깊이와 공간감을 유지한다.
    const int32 Clouds = Ultimate || Heavy ? 1 : 0;
    for (int32 I=0; I<Clouds; ++I)
    {
        auto& Smoke = AddAnimated(2,Start+.095f+I*.045f,Ultimate ? .50f : .37f,FVector2D(62.f-I*6.f,68.f+I*6.f)*Strength);
        // 중심은 실제 접촉점에 고정하고, 이후 속도로 양옆/위로 퍼뜨린다.
        Smoke.Offset = TowardCamera*2.f + Side*(I%2 ? 5.f : -5.f)
            +Up*(3.f+I*3.f);
        Smoke.Velocity = Side*(I%2 ? -155.f : 145.f)+Up*(55.f+I*18.f)+Forward*70.f;
        Smoke.Drag = 1.6f;
        Smoke.Angle = (I ? -42.f : 28.f) + Variant*11.f;
    }
    if ((Heavy || Ultimate) && !ImpactSparks)
    {
        ImpactSparks=NewObject<UNiagaraComponent>(this);
        ImpactSparks->SetupAttachment(RootComponent);
        ImpactSparks->SetAutoActivate(false);
        ImpactSparks->SetAsset(SparkSystem);
        ImpactSparks->RegisterComponent();
    }
    if (ImpactSparks && (Heavy || Ultimate))
    {
        ImpactSparks->SetWorldLocation(GetActorLocation());
        ImpactSparks->SetWorldRotation(Forward.Rotation());
        ImpactSparks->Activate(true);
    }
    Duration=FMath::Max(Duration,.45f);
    FHitResult Ground;
    FCollisionObjectQueryParams Objects;Objects.AddObjectTypesToQuery(ECC_WorldStatic);
    const FVector TraceStart=GetActorLocation()+Up*100.f;
    if (GetWorld()->LineTraceSingleByObjectType(Ground,TraceStart,TraceStart-Up*600.f,Objects))
    {
        // 접촉점에서 공격자 반대쪽으로 갈라지는 세 갈래. 크기/색/시간을 분리한다.
        const FVector GroundForward = FVector::VectorPlaneProject(Forward,Ground.ImpactNormal).GetSafeNormal();
        const float Lengths[] = {285.f,205.f,155.f};
        const float Widths[] = {112.f,82.f,58.f};
        const float Angles[] = {0.f,-23.f,31.f};
        const float Hues[] = {0.f,.10f,-.12f};
        const float Palettes[] = {0.f,.48f,.76f,.95f,.55f,.1f,.88f,.7f};
        const int32 PaintCount = Ultimate ? 2 : Heavy ? 1 : 0;
        for (int32 I=0; I<PaintCount; ++I)
        {
            const FVector Spread = GroundForward.RotateAngleAxis(Angles[I],Ground.ImpactNormal);
            const float Length = Lengths[I]*Strength;
            auto& Paint=AddAnimated(4,Start+.045f+I*.035f,.52f+I*.065f,
                FVector2D(Length,Widths[I]*Strength),false);
            Paint.StartSize=FVector2D(Length*.10f,Widths[I]*Strength*.25f);
            Paint.Offset=Ground.ImpactPoint-GetActorLocation()+Ground.ImpactNormal*(2.f+I*.5f);
            Paint.SurfaceExpansionDirection=Spread;
            Paint.ExpansionRate=16.f-I*2.f;
            Paint.Velocity=Spread*(32.f-I*8.f)*Strength;
            Paint.Drag=2.8f;
            Paint.BaseRotation=FRotationMatrix::MakeFromZX(Ground.ImpactNormal,Spread).ToQuat();
            Paint.Material->SetScalarParameterValue(TEXT("HueShift"),Palettes[FMath::Clamp(Variant,0,7)]+Hues[I]);
        }
        const int32 DebrisCount = Ultimate ? 3 : Heavy ? 2 : 2;
        for (int32 I=0; I<DebrisCount; ++I)
        {
            const float Theta = I*2.39996f+Variant*.7f;
            const FVector Radial = Side*FMath::Cos(Theta)+Forward*FMath::Sin(Theta);
            auto& Chip=AddVolume(HifiShard,FLinearColor(.16f,.20f,.28f),Start+.045f+I*.009f,.48f,
                FVector(.35f+I*.025f,.22f,.40f),0);
            Chip.Offset=Radial*5.f;
            Chip.Velocity=Radial*(Ultimate ? 240.f : 150.f)+Up*(145.f+I*13.f);
            Chip.Acceleration=-Up*700.f;
            Chip.Tumble=FRotator(230.f,340.f,140.f);
            if (Ultimate && I==0)
            {
                auto& Puff=AddAnimated(2,Start+.10f+I*.025f,.38f,FVector2D(65.f,50.f));
                Puff.Offset=Ground.ImpactPoint-GetActorLocation()+Up*12.f+Radial*14.f;
                Puff.Velocity=Radial*175.f+Up*25.f;
                Puff.Drag=1.4f;
                Puff.Angle=I*31.f;
            }
        }
    }
    if (Heavy || Ultimate)
    {
        auto& Word=AddAnimated(5,Start+.055f,.31f,FVector2D(Ultimate ? 76.f : 56.f,Ultimate ? 50.f : 38.f)*FMath::Lerp(1.f,SizeGain,.4f));
        Word.Offset=ScreenRight*(-Sign*65.f)+Up*55.f+TowardCamera*16.f;
        Word.Velocity=Up*38.f;Word.Acceleration=-Up*180.f;Word.Angle=-12.f;
    }
}

void AComicCombatEffect::UpdateTrackedRibbon()
{
    ACharacter* Character=Cast<ACharacter>(GetOwner());
    if (!Character || !TrackedRibbon) return;
    bool bChanged=false;
    const float History=AttackVariant==5 ? .11f : .075f;
    while (!RibbonSampleTimes.IsEmpty() && Age-RibbonSampleTimes[0]>History)
    {
        HandSamples.RemoveAt(0,1,EAllowShrinking::No);
        WristSamples.RemoveAt(0,1,EAllowShrinking::No);
        RibbonSampleTimes.RemoveAt(0,1,EAllowShrinking::No);
        bChanged=true;
    }
    if (Age<(AttackVariant==5 ? .22f : .12f))
    {
        const FVector H=UExorcistFaceComponent::StrikeLocation(Character->GetMesh(), AttackVariant)-GetActorLocation();
        const FVector W=UExorcistFaceComponent::StrikeBaseLocation(Character->GetMesh(), AttackVariant)-GetActorLocation();
        // 정지한 손이 새 점으로 판정되지 않도록 확장한 정점 대신 원래 손 위치를 저장한다.
        const float Distance=HandSamples.IsEmpty() ? 0.f : FVector::Distance(HandSamples.Last(),H);
        if (Distance>120.f)
        {
            HandSamples.Reset();WristSamples.Reset();RibbonSampleTimes.Reset();bChanged=true;
        }
        if (HandSamples.IsEmpty() || Distance>3.f)
        {
            if (HandSamples.Num()>=20)
            {
                HandSamples.RemoveAt(0,1,EAllowShrinking::No);
                WristSamples.RemoveAt(0,1,EAllowShrinking::No);
                RibbonSampleTimes.RemoveAt(0,1,EAllowShrinking::No);
            }
            HandSamples.Add(H);
            WristSamples.Add((H-W).GetSafeNormal());
            RibbonSampleTimes.Add(Age);
            bChanged=true;
        }
    }
    TrackedRibbon->SetVisibility(HandSamples.Num()>=2);
    if (bChanged && HandSamples.Num()>=2)
    {
        RibbonVertices.Reset(40);RibbonNormals.Reset(40);RibbonUVs.Reset(40);RibbonIndices.Reset(114);
        for (int32 I=0;I<HandSamples.Num();++I)
        {
            const float U=static_cast<float>(I)/(HandSamples.Num()-1);
            const float Width=(AttackVariant==5 ? 14.f : 9.f)*FMath::Sin(U*PI)*.85f+1.f;
            RibbonVertices.Add(HandSamples[I]-WristSamples[I]*Width*.6f);
            RibbonVertices.Add(HandSamples[I]+WristSamples[I]*Width*.4f);
            RibbonNormals.Add(FVector::UpVector);RibbonNormals.Add(FVector::UpVector);
            RibbonUVs.Add(FVector2D(U,0));RibbonUVs.Add(FVector2D(U,1));
            if (I>0){const int32 B=I*2;RibbonIndices.Append({B-2,B,B-1,B-1,B,B+1});}
        }
        TrackedRibbon->CreateMeshSection_LinearColor(0,RibbonVertices,RibbonIndices,RibbonNormals,RibbonUVs,
            TArray<FLinearColor>(),TArray<FProcMeshTangent>(),false);
    }
    TrackedRibbonMaterial->SetScalarParameterValue(TEXT("Progress"),FMath::Clamp(Age/Duration,0.f,1.f));
}

void AComicCombatEffect::CancelAnticipation()
{
    if (bActive && (CachedKind == EComicEffect::Charge || CachedKind == EComicEffect::Trail)) FinishEffect();
}
