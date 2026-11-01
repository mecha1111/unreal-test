#include "ComicCombatPresentationComponent.h"
#include "ExorcistFaceComponent.h"
#include "Playground.h"
#include "Sound/SoundBase.h"
#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "Components/PointLightComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"

UComicCombatPresentationComponent::UComicCombatPresentationComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UComicCombatPresentationComponent::BeginPlay()
{
	Super::BeginPlay();
	PreviousLocation = GetOwner()->GetActorLocation();
}

void UComicCombatPresentationComponent::BindCamera(UCameraComponent* InCamera, USpringArmComponent* InBoom)
{
	Camera = InCamera;
    if (UMaterialInterface* Outline = LoadObject<UMaterialInterface>(nullptr,
        TEXT("/Game/ExorcistV10/Materials/M_EX_Outline.M_EX_Outline")))
        Camera->AddOrUpdateBlendable(Outline, 1.f);
    // 화면 전체 하이라이트·색 반전은 사용하지 않는다. 캐릭터 외곽선은 유지한다.

	Boom = InBoom;
    const TCHAR* Names[] = {TEXT("Light"), TEXT("Heavy"), TEXT("Ultimate")};
    for (const TCHAR* Name : Names)
    {
        const FString Path = FString::Printf(TEXT("/Game/ComicCombat/Hifi/Audio/S_HF_%s.S_HF_%s"), Name, Name);
        ImpactSounds.Add(LoadObject<USoundBase>(nullptr, *Path));
    }
    WhooshSound = LoadObject<USoundBase>(nullptr, TEXT("/Game/ComicCombat/Hifi/Audio/S_HF_Whoosh.S_HF_Whoosh"));
	BaseOffset = Boom->SocketOffset;
	BaseFov = Camera->FieldOfView;
	BaseArmLength = Boom->TargetArmLength;
	if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
		{
            BaseMeshRotation = Character->GetMesh()->GetRelativeRotation().Quaternion();
            AddTickPrerequisiteComponent(Character->GetCharacterMovement());
            AddTickPrerequisiteComponent(Character->GetMesh());
        }
	Boom->AddTickPrerequisiteComponent(this);
	Boom->CameraLagMaxDistance = 35.f;
	Boom->bUseCameraLagSubstepping = true;
	Boom->CameraLagMaxTimeStep = 1.f / 120.f;
	Boom->bDoCollisionTest = true;
	Boom->ProbeSize = 14.f;
	Camera->PostProcessSettings.bOverride_MotionBlurAmount = true;
	Camera->PostProcessSettings.MotionBlurAmount = 0.f;
	Camera->PostProcessSettings.bOverride_VignetteIntensity = true;
	Camera->PostProcessSettings.VignetteIntensity = 0.f;
	// Keep daylight exposure stable through combat flashes; no camera color filter.
	Camera->PostProcessSettings.bOverride_AutoExposureMinBrightness = true;
	Camera->PostProcessSettings.bOverride_AutoExposureMaxBrightness = true;
	Camera->PostProcessSettings.AutoExposureMinBrightness = 1.f;
	Camera->PostProcessSettings.AutoExposureMaxBrightness = 1.f;
	Camera->PostProcessSettings.bOverride_AutoExposureBias = true;
	Camera->PostProcessSettings.AutoExposureBias = 0.f;
	Camera->PostProcessSettings.bOverride_BloomIntensity = true;
	Camera->PostProcessSettings.BloomIntensity = .38f;
	Camera->PostProcessSettings.bOverride_BloomThreshold = true;
	Camera->PostProcessSettings.BloomThreshold = 1.1f;
	ImpactLight = NewObject<UPointLightComponent>(GetOwner());
	ImpactLight->SetupAttachment(GetOwner()->GetRootComponent());
	ImpactLight->SetCastShadows(false);
	ImpactLight->SetAttenuationRadius(620.f);
	ImpactLight->SetIntensity(0.f);
	ImpactLight->SetVisibility(false);
	ImpactLight->RegisterComponent();

}

void UComicCombatPresentationComponent::PlayCue(EComicEffect Effect, const FVector& Location, int32 Variant, const FVector& Direction)
{
    const FVector EffectDirection = Direction.IsNearlyZero() ? GetOwner()->GetActorForwardVector() : Direction.GetSafeNormal();
	if (Effect == EComicEffect::Question) return;
    if (Effect == EComicEffect::Trail && WhooshSound)
        UGameplayStatics::PlaySoundAtLocation(this, WhooshSound, Location, .55f, Variant >= 3 ? .83f : 1.12f);
	EffectPool.RemoveAll([](const TObjectPtr<AComicCombatEffect>& Entry) { return !IsValid(Entry); });
	for (AComicCombatEffect* Entry : EffectPool)
	{
		if (Entry->CanReuseFor(Effect))
		{
			Entry->SetActorLocation(Location);
			Entry->Initialize(Effect, EffectDirection, Variant, true);
			return;
		}
	}
	FActorSpawnParameters Params;
	Params.Owner = GetOwner();
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	if (AComicCombatEffect* Actor = GetWorld()->SpawnActor<AComicCombatEffect>(
		AComicCombatEffect::StaticClass(), Location, FRotator::ZeroRotator, Params))
	{
		const bool bRetain = EffectPool.Num() < MaxRetainedEffects;
		if (bRetain) EffectPool.Add(Actor);
		Actor->Initialize(Effect, EffectDirection, Variant, bRetain);
	}
}

void UComicCombatPresentationComponent::BeginAttack(int32 Variant)
{
	AttackAge = 0.f;
	FramingVariant = Variant;
}

void UComicCombatPresentationComponent::ConfirmHit(int32 Variant, const FVector& Contact, bool bComboFinish)
{
    const int32 SoundIndex = Variant == 5 ? 2 : Variant >= 2 ? 1 : 0;
    if (ImpactSounds.IsValidIndex(SoundIndex) && ImpactSounds[SoundIndex])
        UGameplayStatics::PlaySoundAtLocation(this, ImpactSounds[SoundIndex], Contact, .8f, Variant % 2 ? .96f : 1.04f);
	KickAge = 0.f;
    bUltimateContactLight = Variant == 5;
	KickStrength = Variant == 5 ? 1.f : Variant >= 2 ? .75f : .52f;
	HitSide = Variant % 2 ? -1.f : 1.f;
	if (ImpactLight)
	{
		ImpactLight->SetWorldLocation(Contact - GetOwner()->GetActorForwardVector() * 5.f);
		const FLinearColor Palettes[] = {FLinearColor(1,.42f,.08f),FLinearColor(.08f,.65f,1),FLinearColor(.8f,.12f,1),FLinearColor(1,.22f,.06f)};
        ImpactLight->SetLightColor(Variant == 5 ? FLinearColor(.12f,.48f,1) :
            (Variant == 0 || Variant == 4) ? FLinearColor(1,.48f,.12f) : Palettes[Variant%4]);
		ImpactLight->SetVisibility(true);
	}

}

void UComicCombatPresentationComponent::OnJump(bool bAirJump)
{
	JumpAge = 0.f;
	LandingAge = 2.f;
	if (ACharacter* Character = Cast<ACharacter>(GetOwner()))
	{
		const FVector Feet = Character->GetActorLocation()
			- FVector(0.f, 0.f, Character->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() - 3.f);
		PlayCue(bAirJump ? EComicEffect::AirJump : EComicEffect::JumpTakeoff, Feet, FootstepIndex++);
	}
}

void UComicCombatPresentationComponent::OnLanding(float DownwardSpeed, const FVector& GroundPoint)
{
	LandingAge = 0.f;
	LandingStrength = FMath::Clamp(DownwardSpeed / 700.f, .35f, 1.f);
	PlayCue(EComicEffect::Landing, GroundPoint + FVector(0.f, 0.f, 3.f), FootstepIndex++);
}

void UComicCombatPresentationComponent::TickComponent(float DeltaTime, ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	APlaygroundCharacter* Player = Cast<APlaygroundCharacter>(GetOwner());
	if (!Player || !Camera || !Boom) return;
    Player->FlushPendingStrikes();
	const FVector Velocity = Player->GetVelocity();
	const float Speed = Velocity.Size2D();
	const bool bFalling = Player->GetCharacterMovement()->IsFalling();
	AttackAge += DeltaTime;
	KickAge += DeltaTime;
    if (SlowEndRealTime >= 0.f && GetWorld()->GetRealTimeSeconds() >= SlowEndRealTime) RestoreTimeDilation();
	JumpAge += DeltaTime;
	LandingAge += DeltaTime;
	const float Envelope = FMath::Square(FMath::Max(0.f, 1.f - KickAge / .24f));
	const float Kick = KickStrength * Envelope;
	if (ImpactLight)
	{
        const float LightFade = FMath::Square(FMath::Max(0.f, 1.f - KickAge / (bUltimateContactLight ? .46f : .28f)));
        const bool Charging = Player->bAttacking && Player->AttackPhase == 0;
        const float ChargeGlow = Charging ? (Player->GetAttackVariant() == 5 ? FMath::Clamp(Player->AttackClipTime/.5f,0.f,1.f)*3200.f : 250.f) : 0.f;
        if (Charging)
        {
            ImpactLight->SetWorldLocation(UExorcistFaceComponent::StrikeLocation(Player->GetMesh(), Player->GetAttackVariant()));
            ImpactLight->SetLightColor(FLinearColor(.12f,.58f,1.f));
        }
        ImpactLight->SetIntensity((bUltimateContactLight ? 16500.f : 11000.f) * KickStrength * LightFade + ChargeGlow);
        ImpactLight->SetVisibility(LightFade > .001f || ChargeGlow > 0.f);
	}
	const bool bUltimate = FramingVariant == 5;
	const bool bDash = Player->bAttacking && Player->GetAttackVariant() == 5 && Player->AttackClipTime >= .55f && Player->AttackClipTime < .88f;
	const float DesiredFraming = 0.f;
	FramingWeight = FMath::FInterpTo(FramingWeight, DesiredFraming, DeltaTime, 9.f);
	const float RunBlend = Player->bRunning && !Player->bAttacking && !bFalling
        ? FMath::Clamp((Speed - Player->JogSpeed) / FMath::Max(1.f,Player->SprintSpeed-Player->JogSpeed), 0.f, 1.f) : 0.f;
	SmoothedRun = FMath::FInterpTo(SmoothedRun, RunBlend, DeltaTime, 5.f);
    Player->GetMesh()->SetRelativeRotation(BaseMeshRotation * FQuat(FVector::ForwardVector,FMath::DegreesToRadians(-SmoothedRun*4.f)));
	const float AirSpeed = bFalling ? FMath::Clamp(FMath::Abs(Velocity.Z) / 750.f, 0.f, 1.f) : 0.f;
    // Free orbit: combat never redirects, offsets or zooms the camera.
    Boom->SocketOffset = BaseOffset;
    Camera->ClearAdditiveOffset();
    Camera->SetFieldOfView(BaseFov + SmoothedRun * 3.f);
	const FVector Location = Player->GetActorLocation();
	const bool bTeleported = FVector::DistSquared(Location, PreviousLocation) > FMath::Square(350.f);
	PreviousLocation = Location;
    // 달리기 접지가 필요하지 않은 프레임은 소켓 조회와 두 번의 바닥 트레이스를 생략한다.
    if (bTeleported || Speed < 420.f || bFalling || Player->bAttacking)
    {
        FootArmed[0] = FootArmed[1] = false;
        FootPreviousHeight[0] = FootPreviousHeight[1] = 100.f;
        return;
    }
    // 실제 발이 떠올랐다가 내려오는 접지 전이에서만 스폰한다. 고정 주기 교대 스폰은 사용하지 않는다.
    for (int32 I=0; I<2; ++I)
    {
        const FVector Foot = Player->GetMesh()->GetSocketLocation(I ? TEXT("foot_r") : TEXT("foot_l"));
        FHitResult Ground;
        FCollisionQueryParams Query(SCENE_QUERY_STAT(ComicFootPlant),false,Player);
        const bool GroundFound = GetWorld()->LineTraceSingleByChannel(Ground,Foot+FVector(0,0,24),Foot-FVector(0,0,95),ECC_Visibility,Query);
        const float Height = GroundFound ? Foot.Z-Ground.ImpactPoint.Z : 100.f;
        if (bTeleported || Speed < 420.f || bFalling || Player->bAttacking)
        {
            FootArmed[I] = false;
        }
        else
        {
            if (Height > 25.f) FootArmed[I] = true;
            const float Now = GetWorld()->GetTimeSeconds();
            if (GroundFound && FootArmed[I] && Height <= 19.f && Height <= FootPreviousHeight[I] && Now-FootLastSpawn[I] > .12f)
            {
                LastFootPlant = Ground.ImpactPoint + Ground.ImpactNormal*2.f;
                PlayCue(EComicEffect::Speed,LastFootPlant,I);
                ++FootPlantCount;
                FootLastSpawn[I] = Now;
                FootArmed[I] = false;
            }
        }
        FootPreviousHeight[I] = Height;
    }
}

void UComicCombatPresentationComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	for (AComicCombatEffect* Effect : EffectPool)
	{
		if (IsValid(Effect)) Effect->Destroy();
	}
	EffectPool.Reset();
	if (Boom)
	{
		Boom->SocketOffset = BaseOffset;
		Boom->TargetArmLength = BaseArmLength;
	}
	if (Camera)
	{
		Camera->SetFieldOfView(BaseFov);
		Camera->ClearAdditiveOffset();
	}
    RestoreTimeDilation();
	Super::EndPlay(EndPlayReason);
}

void UComicCombatPresentationComponent::RestoreTimeDilation()
{
    if (SlowEndRealTime < 0.f) return;
    UGameplayStatics::SetGlobalTimeDilation(this,PreviousTimeDilation);
    SlowEndRealTime = -1.f;
}

void UComicCombatPresentationComponent::CancelPresentation()
{
    RestoreTimeDilation();
    UltimateFlashAge = 10.f;
    FramingWeight *= .5f;
    for (AComicCombatEffect* Effect : EffectPool)
    {
        if (IsValid(Effect)) Effect->CancelAnticipation();
    }
    if (ComicMaterial)
    {
        ComicMaterial->SetScalarParameterValue(TEXT("ImpactFlash"),0.f);
        ComicMaterial->SetScalarParameterValue(TEXT("NegativeAmount"),0.f);
        Camera->AddOrUpdateBlendable(ComicMaterial,0.f);
    }
}
