#include "ComicCombatPresentationComponent.h"
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
            AddTickPrerequisiteComponent(Character->GetCharacterMovement());
            AddTickPrerequisiteComponent(Character->GetMesh());
        }
	Boom->AddTickPrerequisiteComponent(this);
	Boom->CameraLagMaxDistance = 55.f;
	Boom->bUseCameraLagSubstepping = true;
	Boom->CameraLagMaxTimeStep = 1.f / 120.f;
	Boom->bDoCollisionTest = true;
	Boom->ProbeSize = 14.f;
	Camera->PostProcessSettings.bOverride_MotionBlurAmount = true;
	Camera->PostProcessSettings.MotionBlurAmount = 0.f;
	Camera->PostProcessSettings.bOverride_VignetteIntensity = true;
	Camera->PostProcessSettings.VignetteIntensity = .12f;
	// 노출을 고정해 어두운 무대가 자동으로 밝아지거나 섬광 뒤에 조명이 펌핑되지 않게 한다.
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
	if (UMaterialInterface* Comic = LoadObject<UMaterialInterface>(nullptr,
		TEXT("/Game/ComicCombat/Materials/M_CC_ComicPost.M_CC_ComicPost")))
	{
		ComicMaterial = UMaterialInstanceDynamic::Create(Comic, this);
		Camera->AddOrUpdateBlendable(ComicMaterial, 1.f);
	}
}

void UComicCombatPresentationComponent::PlayCue(EComicEffect Effect, const FVector& Location, int32 Variant)
{
	if (Effect == EComicEffect::Question) return;
    if (Effect == EComicEffect::Trail && WhooshSound)
        UGameplayStatics::PlaySoundAtLocation(this, WhooshSound, Location, .55f, Variant >= 3 ? .83f : 1.12f);
	EffectPool.RemoveAll([](const TObjectPtr<AComicCombatEffect>& Entry) { return !IsValid(Entry); });
	for (AComicCombatEffect* Entry : EffectPool)
	{
		if (Entry->CanReuseFor(Effect))
		{
			Entry->SetActorLocation(Location);
			Entry->Initialize(Effect, GetOwner()->GetActorForwardVector(), Variant, true);
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
		Actor->Initialize(Effect, GetOwner()->GetActorForwardVector(), Variant, bRetain);
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
	KickStrength = Variant == 5 ? 1.f : Variant >= 2 ? .75f : .52f;
	HitSide = Variant % 2 ? -1.f : 1.f;
	if (ImpactLight)
	{
		ImpactLight->SetWorldLocation(Contact - GetOwner()->GetActorForwardVector() * 20.f + FVector(0.f, 0.f, 15.f));
		const FLinearColor Palettes[] = {FLinearColor(1,.42f,.08f),FLinearColor(.08f,.65f,1),FLinearColor(.8f,.12f,1),FLinearColor(1,.22f,.06f)};
        ImpactLight->SetLightColor(Variant == 5 ? FLinearColor(.25f,.6f,1) : Variant == 7 ? FLinearColor(.7f,.2f,1) : Palettes[Variant%4]);
		ImpactLight->SetVisibility(true);
	}
	if (Variant == 5 || Variant == 7 || bComboFinish)
    {
        FlashDuration = Variant == 5 ? .72f : Variant == 7 ? .58f : .44f;
        if (SlowEndRealTime < 0.f) PreviousTimeDilation = UGameplayStatics::GetGlobalTimeDilation(this);
        UGameplayStatics::SetGlobalTimeDilation(this,PreviousTimeDilation*.22f);
        SlowEndRealTime = GetWorld()->GetRealTimeSeconds()+FlashDuration;
        UltimateFlashAge = 0.f;
		if (ComicMaterial)
		{
			ComicMaterial->SetScalarParameterValue(TEXT("ImpactFlash"), 1.f);
			if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
			{
				FVector2D Screen;
				int32 Width = 0, Height = 0;
				PC->GetViewportSize(Width, Height);
				if (Width > 0 && Height > 0 && PC->ProjectWorldLocationToScreen(Contact, Screen, true))
					ComicMaterial->SetVectorParameterValue(TEXT("ImpactCenter"),
						FLinearColor(Screen.X / Width, Screen.Y / Height, 0.f, 0.f));
			}
		}
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
	const FVector Velocity = Player->GetVelocity();
	const float Speed = Velocity.Size2D();
	const bool bFalling = Player->GetCharacterMovement()->IsFalling();
	AttackAge += DeltaTime;
	KickAge += DeltaTime;
    // 화면 반전은 실시간으로 감쇠한다. 월드의 캐릭터와 VFX는 실제 슬로모션 시간으로 진행한다.
    UltimateFlashAge += DeltaTime / FMath::Max(.01f,UGameplayStatics::GetGlobalTimeDilation(this));
    if (SlowEndRealTime >= 0.f && GetWorld()->GetRealTimeSeconds() >= SlowEndRealTime) RestoreTimeDilation();
	JumpAge += DeltaTime;
	LandingAge += DeltaTime;
	const float Envelope = FMath::Square(FMath::Max(0.f, 1.f - KickAge / .24f));
	const float Kick = KickStrength * Envelope;
	if (ImpactLight)
	{
		const float LightFade = FMath::Square(FMath::Max(0.f, 1.f - KickAge / .28f));
        const bool Charging = Player->bAttacking && Player->AttackPhase == 0;
        const float ChargeGlow = Charging ? (Player->GetAttackVariant() == 5 ? FMath::Clamp(Player->AttackClipTime/.5f,0.f,1.f)*3200.f : 250.f) : 0.f;
        if (Charging)
        {
            ImpactLight->SetWorldLocation(Player->GetMesh()->GetSocketLocation(TEXT("hand_r")));
            ImpactLight->SetLightColor(FLinearColor(.12f,.58f,1.f));
        }
        ImpactLight->SetIntensity(11000.f * KickStrength * LightFade + ChargeGlow);
        ImpactLight->SetVisibility(LightFade > .001f || ChargeGlow > 0.f);
	}
	const bool bUltimate = FramingVariant == 5;
	const bool bDash = Player->bAttacking && Player->GetAttackVariant() == 5 && Player->AttackClipTime >= .55f && Player->AttackClipTime < .88f;
	const float DesiredFraming = Player->bAttacking ? (bUltimate ? 1.f : .65f) : 0.f;
	FramingWeight = FMath::FInterpTo(FramingWeight, DesiredFraming, DeltaTime, 9.f);
	const float RunBlend = FMath::Clamp((Speed - 280.f) / 480.f, 0.f, 1.f);
	SmoothedRun = FMath::FInterpTo(SmoothedRun, RunBlend, DeltaTime, 5.f);
	const float AirSpeed = bFalling ? FMath::Clamp(FMath::Abs(Velocity.Z) / 750.f, 0.f, 1.f) : 0.f;
	if (ComicMaterial)
	{
		ComicMaterial->SetScalarParameterValue(TEXT("ImpactFlash"), UltimateFlashAge >= .035f && UltimateFlashAge < .085f ? 1.f : 0.f);
        const float Negative = UltimateFlashAge < FlashDuration*.6f ? 1.f : FMath::Clamp((FlashDuration-UltimateFlashAge)/(FlashDuration*.4f),0.f,1.f);
        ComicMaterial->SetScalarParameterValue(TEXT("NegativeAmount"),Negative);
        const float Charging = Player->bAttacking && Player->AttackPhase == 0 ? (bUltimate ? .9f : .25f) : 0.f;
        ComicMaterial->SetScalarParameterValue(TEXT("ChargeAmount"),Charging);
		ComicMaterial->SetScalarParameterValue(TEXT("SpeedAmount"), bDash ? 1.f : FMath::Max(SmoothedRun * .65f, AirSpeed * .6f));
		ComicMaterial->SetScalarParameterValue(TEXT("HitAccent"), Kick * .32f);
		ComicMaterial->SetScalarParameterValue(TEXT("ImpactDarken"), FMath::Min(.36f, KickStrength * .45f) * FMath::Max(0.f, 1.f - KickAge / .25f));
	}
	// 상승 시 상체 위 공간을 확보하고 하강 시 착지점을 향한다. 입력 회전은 덮어쓰지 않는다.
	const float DesiredAirPitch = bFalling ? FMath::Clamp(Velocity.Z / 180.f, -5.f, 3.f) : 0.f;
	AirPitch = FMath::FInterpTo(AirPitch, DesiredAirPitch, DeltaTime, 6.f);
	AirOffset = FMath::FInterpTo(AirOffset, bFalling ? FMath::Clamp(Velocity.Z * .025f, -15.f, 18.f) : 0.f, DeltaTime, 7.f);
	const float LandingPulse = LandingAge < .4f
		? FMath::Sin(LandingAge / .4f * UE_PI * 2.f) * FMath::Exp(-LandingAge * 7.f) * LandingStrength : 0.f;
	const float JumpPulse = FMath::Exp(-JumpAge * 14.f);
	StridePhase += DeltaTime * 20.f;
	const float Bob = !bFalling && !Player->bAttacking ? FMath::Sin(StridePhase) * SmoothedRun : 0.f;
	Boom->SocketOffset = BaseOffset + FVector(-SmoothedRun * 14.f,
		FramingWeight * 320.f + FMath::Sin(KickAge * 55.f) * Kick * HitSide * 7.f,
		FramingWeight * 8.f - SmoothedRun * 10.f + AirOffset - LandingPulse * 24.f + Bob * 1.3f);
	const float WindupPullback = Player->bAttacking && bUltimate && Player->AttackClipTime < .55f ? 45.f : 0.f;
	const float DesiredArm = BaseArmLength + SmoothedRun * 48.f + (bDash ? 35.f : 0.f)
		+ FramingWeight * (WindupPullback - 70.f) - Kick * 24.f + JumpPulse * 12.f;
	Boom->TargetArmLength = FMath::FInterpTo(Boom->TargetArmLength, DesiredArm, DeltaTime, 9.f);
	// 감쇠하는 방향성 충격. 카메라 위치는 스프링암 충돌 결과 안에 유지한다.
	FRotator DesiredRotation = Camera->GetComponentRotation();
	DesiredRotation.Pitch += AirPitch - LandingPulse * 2.4f + JumpPulse * 1.1f
		+ FMath::Cos(KickAge * 48.f) * Kick * 2.4f;
	DesiredRotation.Yaw += -FramingWeight * 30.f + FMath::Sin(KickAge * 59.f) * Kick * HitSide * 1.5f;
	DesiredRotation.Roll += FMath::Sin(KickAge * 46.f) * Kick * HitSide * 1.25f + Bob * .12f;
	const FQuat LocalAdjustment = Camera->GetComponentQuat().Inverse() * DesiredRotation.Quaternion();
	Camera->ClearAdditiveOffset();
	Camera->AddAdditiveOffset(FTransform(LocalAdjustment), 0.f);
	const float DesiredFov = BaseFov + SmoothedRun * 11.f + (bDash ? 9.f : 0.f)
		+ AirSpeed * 2.f - FramingWeight * 5.f - Kick * 4.f - LandingPulse * 1.5f;
	Camera->SetFieldOfView(FMath::FInterpTo(Camera->FieldOfView, DesiredFov, DeltaTime, 14.f));
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
            if (Height > 16.f) FootArmed[I] = true;
            const float Now = GetWorld()->GetTimeSeconds();
            if (GroundFound && FootArmed[I] && Height <= 13.f && Height <= FootPreviousHeight[I] && Now-FootLastSpawn[I] > .12f)
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
        ComicMaterial->SetScalarParameterValue(TEXT("ChargeAmount"),0.f);
    }
}
