#include "Playground.h"
#include "ExorcistFaceComponent.h"
#include "ComicSteppedMeshComponent.h"
#include "ComicCombatPresentationComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "AlphaBlend.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Font.h"
#include "Engine/FontFace.h"
#include "Engine/Texture2D.h"
#include "CanvasItem.h"
#include "CanvasTypes.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputKeyEventArgs.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

APlaygroundCharacter::APlaygroundCharacter(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
    PrimaryActorTick.bCanEverTick = true;
    GetCapsuleComponent()->InitCapsuleSize(42.f, 96.f);
    bUseControllerRotationYaw = false;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0.f, 900.f, 0.f);
    GetCharacterMovement()->MaxWalkSpeed = JogSpeed;
    GetCharacterMovement()->JumpZVelocity = 620.f;
    JumpMaxCount = 2;
    GetCharacterMovement()->GravityScale = 1.5f;
    GetCharacterMovement()->AirControl = .72f;
    GetCharacterMovement()->BrakingDecelerationWalking = 2800.f;
    GetCharacterMovement()->MaxAcceleration = 3200.f;
    GetCharacterMovement()->GroundFriction = 6.f;
    GetCharacterMovement()->bUseSeparateBrakingFriction = true;
    GetCharacterMovement()->BrakingFriction = 4.f;
    GetCharacterMovement()->BrakingFrictionFactor = 1.f;
    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(RootComponent);
    CameraBoom->TargetArmLength = 540.f;
    CameraBoom->SocketOffset = FVector(0.f, 12.f, 45.f);
    CameraBoom->bUsePawnControlRotation = true;
    CameraBoom->bEnableCameraLag = true;
    CameraBoom->bEnableCameraRotationLag = false;
    CameraBoom->CameraLagSpeed = 18.f;
    FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
    FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    FollowCamera->FieldOfView = 78.f;
    FollowCamera->bUsePawnControlRotation = false;
    ExorcistFace = CreateDefaultSubobject<UExorcistFaceComponent>(TEXT("ExorcistFace"));
    CombatPresentation = CreateDefaultSubobject<UComicCombatPresentationComponent>(TEXT("CombatPresentation"));
    GetMesh()->SetRenderCustomDepth(true);
    GetMesh()->SetCustomDepthStencilValue(11);
    // CharacterMovement keeps the capsule about 2.15 cm above its floor.
    GetMesh()->SetRelativeLocation(FVector(0.f, 0.f, -98.f));
    GetMesh()->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));
    // 발 소켓 VFX와 공격 포즈는 뷰포트가 가려져도 현재 프레임의 뼈를 사용한다.
    GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> Manny(TEXT("/Game/ExorcistV10/Character/SK_EX_Optimized.SK_EX_Optimized"));
    if (Manny.Succeeded()) GetMesh()->SetSkeletalMesh(Manny.Object);
    static ConstructorHelpers::FClassFinder<UAnimInstance> Animation(TEXT("/Game/ExorcistV10/Animations/manny/ABP_CC_Unarmed"));
    if (Animation.Succeeded()) GetMesh()->SetAnimInstanceClass(Animation.Class);
    static ConstructorHelpers::FObjectFinder<UAnimSequence> Attack1(TEXT("/Game/ExorcistV10/Animations/manny/A_CC_Jab.A_CC_Jab"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> Attack2(TEXT("/Game/ExorcistV10/Animations/manny/A_CC_Cross.A_CC_Cross"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> Attack3(TEXT("/Game/ExorcistV10/Animations/manny/A_CC_Uppercut.A_CC_Uppercut"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> Heavy(TEXT("/Game/ExorcistV10/Animations/manny/A_CC_Hammer.A_CC_Hammer"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> Dash(TEXT("/Game/ExorcistV10/Animations/manny/A_CC_DashStrike.A_CC_DashStrike"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> Ultimate(TEXT("/Game/ExorcistV10/Animations/manny/A_CC_InkBreaker.A_CC_InkBreaker"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> Aerial(TEXT("/Game/ExorcistV10/Animations/manny/A_HF_AerialStrike.A_HF_AerialStrike"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> Rising(TEXT("/Game/ExorcistV10/Animations/manny/A_CC_RisingPunch.A_CC_RisingPunch"));
    AttackAnimations = {Attack1.Object, Attack2.Object, Attack3.Object, Heavy.Object, Dash.Object, Ultimate.Object, Aerial.Object, Rising.Object};
    static ConstructorHelpers::FObjectFinder<UAnimSequence> JumpClip(TEXT("/Game/ExorcistV10/Animations/manny/A_CC_JumpLift.A_CC_JumpLift"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> AirClip(TEXT("/Game/ExorcistV10/Animations/manny/A_CC_AirKick.A_CC_AirKick"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> LandClip(TEXT("/Game/ExorcistV10/Animations/manny/A_CC_Land.A_CC_Land"));
    MovementAnimations = {JumpClip.Object, AirClip.Object, LandClip.Object};
}

void APlaygroundCharacter::BeginPlay()
{
    Super::BeginPlay();
    CombatPresentation->BindCamera(FollowCamera, CameraBoom);
    if (UAnimInstance* Anim = GetMesh()->GetAnimInstance()) Anim->SetRootMotionMode(ERootMotionMode::IgnoreRootMotion);
    if (APlayerController* PC = Cast<APlayerController>(Controller))
    {
        PC->SetControlRotation(FRotator(-16.f, 0.f, 0.f));
        PC->SetInputMode(FInputModeGameOnly());
        PC->bShowMouseCursor = false;
    }
}

void APlaygroundCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    UEnhancedInputComponent* Enhanced = Cast<UEnhancedInputComponent>(Input);
    APlayerController* PC = Cast<APlayerController>(Controller);
    if (!Enhanced || !PC || !PC->GetLocalPlayer()) return;
    Mapping = NewObject<UInputMappingContext>(this);
    auto Action = [this](EInputActionValueType Type)
    {
        UInputAction* Result = NewObject<UInputAction>(this);
        Result->ValueType = Type;
        return Result;
    };
    MoveAction = Action(EInputActionValueType::Axis2D);
    MoveAction->AccumulationBehavior = EInputActionAccumulationBehavior::Cumulative;
    LookAction = Action(EInputActionValueType::Axis2D);
    JumpAction = Action(EInputActionValueType::Boolean);
    AttackAction = Action(EInputActionValueType::Boolean);
    RunAction = Action(EInputActionValueType::Boolean);
    HeavyAction = Action(EInputActionValueType::Boolean);
    DashAction = Action(EInputActionValueType::Boolean);
    UltimateAction = Action(EInputActionValueType::Boolean);
    PoseStepAction = Action(EInputActionValueType::Boolean);
    CancelAction = Action(EInputActionValueType::Boolean);
    Mapping->MapKey(MoveAction, EKeys::D);
    Mapping->MapKey(MoveAction, EKeys::A).Modifiers.Add(NewObject<UInputModifierNegate>(Mapping));
    auto& Forward = Mapping->MapKey(MoveAction, EKeys::W);
    Forward.Modifiers.Add(NewObject<UInputModifierSwizzleAxis>(Mapping));
    auto& Back = Mapping->MapKey(MoveAction, EKeys::S);
    Back.Modifiers.Add(NewObject<UInputModifierNegate>(Mapping));
    Back.Modifiers.Add(NewObject<UInputModifierSwizzleAxis>(Mapping));
    // Mouse look is handled by the controller independently of combat actions.
    Mapping->MapKey(JumpAction, EKeys::SpaceBar);
    Mapping->MapKey(AttackAction, EKeys::LeftMouseButton);
    Mapping->MapKey(AttackAction, EKeys::V); // 임시 검증 키: HUD 안내에는 표시하지 않는다.
    Mapping->MapKey(HeavyAction, EKeys::RightMouseButton);
    Mapping->MapKey(HeavyAction, EKeys::B); // 임시 검증 키: HUD 안내에는 표시하지 않는다.
    Mapping->MapKey(DashAction, EKeys::E);
    Mapping->MapKey(UltimateAction, EKeys::Q);
    Mapping->MapKey(CancelAction, EKeys::LeftControl);
    Mapping->MapKey(CancelAction, EKeys::RightControl);
    Mapping->MapKey(RunAction, EKeys::LeftShift);
    Mapping->MapKey(RunAction, EKeys::RightShift);
    PC->GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>()->AddMappingContext(Mapping, 0);
    Enhanced->BindAction(MoveAction, ETriggerEvent::Triggered, this, &APlaygroundCharacter::Move);
    Enhanced->BindAction(LookAction, ETriggerEvent::Triggered, this, &APlaygroundCharacter::Look);
    Enhanced->BindAction(JumpAction, ETriggerEvent::Started, this, &APlaygroundCharacter::JumpPressed);
    Enhanced->BindAction(JumpAction, ETriggerEvent::Completed, this, &ACharacter::StopJumping);
    Enhanced->BindAction(RunAction, ETriggerEvent::Started, this, &APlaygroundCharacter::StartRun);
    Enhanced->BindAction(RunAction, ETriggerEvent::Completed, this, &APlaygroundCharacter::StopRun);
    Enhanced->BindAction(RunAction, ETriggerEvent::Canceled, this, &APlaygroundCharacter::StopRun);
    Enhanced->BindAction(AttackAction, ETriggerEvent::Started, this, &APlaygroundCharacter::Attack);
    Enhanced->BindAction(HeavyAction, ETriggerEvent::Started, this, &APlaygroundCharacter::HeavyAttack);
    Enhanced->BindAction(DashAction, ETriggerEvent::Started, this, &APlaygroundCharacter::DashAttack);
    Enhanced->BindAction(UltimateAction, ETriggerEvent::Started, this, &APlaygroundCharacter::UltimateAttack);
    Enhanced->BindAction(CancelAction, ETriggerEvent::Started, this, &APlaygroundCharacter::CancelAttack);
}

void APlaygroundCharacter::PawnClientRestart()
{
    Super::PawnClientRestart();
    if (APlayerController* PC = Cast<APlayerController>(Controller))
    {
        PC->SetControlRotation(FRotator(-16.f, 0.f, 0.f));
        PC->SetInputMode(FInputModeGameOnly());
        PC->bShowMouseCursor = false;
    }
}

void APlaygroundCharacter::Move(const FInputActionValue& Value)
{
    if (!Controller) return;
    const FVector2D Axis = Value.Get<FVector2D>().GetClampedToMaxSize(1.f);
    const FRotator Yaw(0.f, Controller->GetControlRotation().Yaw, 0.f);
    MoveIntent = FRotationMatrix(Yaw).GetUnitAxis(EAxis::X)*Axis.Y + FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y)*Axis.X;
    LastMoveInputAt = GetWorld()->GetTimeSeconds();
    // 회복 구간은 이동으로 즉시 끊는다. 준비와 접촉 중에는 방향 입력을 다음 공격에 보관한다.
    if (bAttacking && AttackPhase == 3 && !MoveIntent.IsNearlyZero()) CancelAttack();
    if (PoseHoldUntil > GetWorld()->GetTimeSeconds()) return;
    const float MoveScale = bAttacking ? (ActiveAttack >= 3 ? 0.f : .35f) : 1.f;
    AddMovementInput(MoveIntent, MoveScale);
}

void APlaygroundCharacter::Look(const FInputActionValue& Value)
{
    const FVector2D Axis = Value.Get<FVector2D>();
    AddControllerYawInput(Axis.X * .12f);
    AddControllerPitchInput(-Axis.Y * .12f);
}

void APlaygroundCharacter::StartRun()
{
    bRunning = true;
    GetCharacterMovement()->MaxWalkSpeed = SprintSpeed;
}

void APlaygroundCharacter::StopRun()
{
    // 키를 떼거나 액션이 취소되면 즉시 걷기로 복귀한다.
    bRunning = false;
    GetCharacterMovement()->MaxWalkSpeed = JogSpeed;
}

void APlaygroundCharacter::Attack() { RequestAction(0); }
void APlaygroundCharacter::HeavyAttack() { RequestAction(1); }
void APlaygroundCharacter::DashAttack() { RequestAction(4); }
void APlaygroundCharacter::UltimateAttack() { RequestAction(5); }
float APlaygroundCharacter::GetUltimateCooldown() const { return 0.f; }
void APlaygroundCharacter::JumpPressed()
{
    if (bAttacking) CancelAttack();
    Jump();
}

void APlaygroundCharacter::OnJumped_Implementation()
{
    Super::OnJumped_Implementation();
    const bool bAirJump = JumpCurrentCount > 1;
    CombatPresentation->OnJump(bAirJump);
    PlayMovementAnimation(bAirJump ? 1 : 0);
}

void APlaygroundCharacter::Landed(const FHitResult& Hit)
{
    const float DownwardSpeed = FMath::Max(0.f, -GetVelocity().Z);
    Super::Landed(Hit);
    if (bAttacking && ActiveAttack == 6 && bAwaitingLanding)
    {
        bAwaitingLanding = false;
        GetMesh()->GlobalAnimRateScale = 1.f;
        bStrikeResolved = true;
        ResolveAttack();
    }
    if (DownwardSpeed > 220.f)
    {
        CombatPresentation->OnLanding(DownwardSpeed, Hit.ImpactPoint);
        if (!bAttacking)
        {
            // 이동 착지는 전신 착지 클립으로 달리기를 덮지 않는다.
            if (GetVelocity().SizeSquared2D() > FMath::Square(120.f))
            {
                if (UAnimInstance* Anim = GetMesh()->GetAnimInstance())
                    if (MovementMontage) Anim->Montage_Stop(.10f, MovementMontage);
                MovementMontage = nullptr;
            }
            else PlayMovementAnimation(2);
        }
    }
}

void APlaygroundCharacter::PlayMovementAnimation(int32 Index)
{
    if (!MovementAnimations.IsValidIndex(Index) || !MovementAnimations[Index]) return;
    if (UAnimInstance* Anim = GetMesh()->GetAnimInstance())
    {
        // 이동 몽타주는 공격 상태/노티파이를 변경하지 않고 기본 이동 포즈로 블렌딩된다.
        MovementMontage = Anim->PlaySlotAnimationAsDynamicMontage(MovementAnimations[Index], TEXT("DefaultSlot"), .065f, .12f);
    }
}

void APlaygroundCharacter::StartAttack(int32 Variant)
{
    if (Variant == 5 && UltimateCharge < 99.99f) return;
    if (GetCharacterMovement()->IsFalling() && Variant != 6) return;
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    UAnimSequence* Sequence = AttackAnimations.IsValidIndex(Variant) ? AttackAnimations[Variant].Get() : nullptr;
    if (!Anim || !Sequence) return;
    RestorePoseRate();
    UAnimMontage* PreviousMontage = ActiveMontage;
    ActiveMontage = nullptr;
    const bool bLinking = PreviousMontage != nullptr;
    bContinuousAttack = bLinking && Variant < 4;
    // 이전 동작의 속도를 유지하며 다음 준비 자세와 교차 블렌딩한다.
    // 지연 노티파이는 HandleCombatCue의 출처 검사로 차단한다.
    MovementMontage = nullptr;
    ChainBlendUntil = bLinking ? GetWorld()->GetTimeSeconds()+.10f : -1.f;
    const float Now = GetWorld()->GetTimeSeconds();
    FVector Aim = Controller ? FRotator(0.f,Controller->GetControlRotation().Yaw,0.f).Vector() : GetActorForwardVector();
    if (Now-LastMoveInputAt < .18f && !MoveIntent.IsNearlyZero()) Aim = MoveIntent.GetSafeNormal2D();
    AssistedTarget = FindAssistedTarget(Aim,Variant == 5 ? 800.f : 330.f,Variant == 5 ? .35f : .55f);
    if (AssistedTarget.IsValid()) Aim = (AssistedTarget->GetActorLocation()-GetActorLocation()).GetSafeNormal2D();
    SetActorRotation(Aim.Rotation());
    const float EntryTime = bLinking && Variant < 4 ? .0333f : 0.f;
    FAlphaBlendArgs BlendIn(bLinking ? (Variant == 3 ? .16f : .10f) : .065f);
    BlendIn.BlendOption = EAlphaBlendOption::HermiteCubic;
    FAlphaBlendArgs BlendOut(.14f);
    BlendOut.BlendOption = EAlphaBlendOption::HermiteCubic;
    ActiveMontage = Anim->PlaySlotAnimationAsDynamicMontage_WithBlendArgs(Sequence,
        TEXT("DefaultSlot"), BlendIn, BlendOut, 1.f, 1, -1.f, EntryTime);
    if (!ActiveMontage) { FinishAttack(); return; }
    if (Variant == 5) UltimateCharge = 0.f;
    FOnMontageEnded EndDelegate;
    EndDelegate.BindUObject(this, &APlaygroundCharacter::OnAttackEnded);
    Anim->Montage_SetEndDelegate(EndDelegate, ActiveMontage);
    bAttacking = true;
    bCanChain = false;
    bStrikeResolved = false;
    PendingStrikes.Reset();
    bAwaitingLanding = false;
    FlurryHit = -1;
    AttackPhase = 0;
    LungeProgress = 0.f;
    if (UComicSteppedMeshComponent* Stepped = Cast<UComicSteppedMeshComponent>(GetMesh())) Stepped->ResetPoseCadence();
    BufferedUntil = -1.f;
    BufferedAction = -1;
    ActiveAttack = Variant;
    CombatPresentation->BeginAttack(Variant);
    if (bStartingLight) LightChain = (LightChain + 1) % 3;
    else LightChain = 0;
    ComboIndex = Variant < 3 ? (Variant + 1) % 3 : 0;
    GetCharacterMovement()->bOrientRotationToMovement = false;
    LastAttackTime = GetWorld()->GetTimeSeconds();
    ++AttackCount;
    if (Variant == 4)
    {
        DashReadyAt = LastAttackTime + 2.4f;
        GetCharacterMovement()->StopMovementImmediately();
    }
    if (Variant == 5)
    {
        GetCharacterMovement()->StopMovementImmediately();

    }
    CombatPresentation->PlayCue(EComicEffect::Charge, UExorcistFaceComponent::StrikeLocation(GetMesh(), Variant), Variant);
}

void APlaygroundCharacter::HandleCombatCue(int32 Cue, UAnimSequenceBase* SourceAnimation)
{
    if (!bAttacking) return;
    // 이전 클립의 지연 노티파이가 취소 후 새 공격을 발동시키지 않도록 출처를 검증한다.
    if (SourceAnimation != ActiveMontage && (!AttackAnimations.IsValidIndex(ActiveAttack) || SourceAnimation != AttackAnimations[ActiveAttack])) return;
    if (Cue == 30 && ActiveAttack == 5)
    {
        AttackPhase = 1;
        DashUntil = GetWorld()->GetTimeSeconds() + .29f;
        GetCharacterMovement()->MaxWalkSpeed = 2400.f;
        CombatPresentation->PlayCue(EComicEffect::Rush, GetActorLocation(), 5);
        return;
    }
    if (Cue >= 10 && Cue <= 14 && ActiveAttack == 4)
    {
        const int32 Index = Cue - 10;
        if (Index <= FlurryHit) return;
        FlurryHit = Index;
        bStrikeResolved = true;
        AttackPhase = 2;
        AddActorWorldOffset(GetActorForwardVector() * 8.f, true);
        PendingStrikes.Add(FlurryHit);
        return;
    }
    if (Cue == 0 || (Cue >= 20 && Cue <= 24 && ActiveAttack == 4))
    {
        AttackPhase = 1;
        CombatPresentation->PlayCue(EComicEffect::Trail,
            UExorcistFaceComponent::StrikeLocation(GetMesh(), ActiveAttack == 4 ? (Cue == 24 ? 2 : FMath::Max(0, Cue - 20) % 2) : ActiveAttack),
            ActiveAttack == 4 ? (Cue == 24 ? 2 : FMath::Max(0, Cue - 20) % 2) : ActiveAttack);
    }
    else if (Cue == 1 && !bStrikeResolved)
    {
        // 공중 타격의 마지막 포즈만 유지한다. 실제 판정과 충격은 착지 콜백에서 일치시킨다.
        if (ActiveAttack == 6 && GetCharacterMovement()->IsFalling())
        {
            bAwaitingLanding = true;
            GetMesh()->GlobalAnimRateScale = 0.f;
            return;
        }
        bStrikeResolved = true;
        AttackPhase = 2;
        PendingStrikes.Add(-1);
        if (ActiveAttack == 7) bRisePending = true;
    }
    else if (Cue == 2)
    {
        AttackPhase = 3;
        CombatPresentation->PlayCue(EComicEffect::Recovery, UExorcistFaceComponent::StrikeLocation(GetMesh(), GetImpactVariant()), GetImpactVariant());
        bCanChain = true;

    }
}

void APlaygroundCharacter::FlushPendingStrikes()
{
    if (!bAttacking) { PendingStrikes.Reset(); return; }
    const int32 LatestFlurryHit = FlurryHit;
    for (int32 Pending : PendingStrikes)
    {
        if (ActiveAttack == 4) FlurryHit = Pending;
        ResolveAttack();
    }
    FlurryHit = LatestFlurryHit;
    PendingStrikes.Reset();
}

void APlaygroundCharacter::ResolveAttack()
{
    const FVector Start = GetActorLocation() + GetActorForwardVector() * 35.f;
    const bool bUltimate = ActiveAttack == 5;
    const int32 ImpactVariant = GetImpactVariant();
    const FVector StrikePoint = UExorcistFaceComponent::StrikeLocation(GetMesh(), ImpactVariant);
    LastStrikePoint = StrikePoint;
    const FVector End = Start + GetActorForwardVector() * (bUltimate ? 245.f : ActiveAttack == 7 ? 170.f : 155.f);
    FCollisionObjectQueryParams Objects;
    Objects.AddObjectTypesToQuery(ECC_WorldDynamic);
    Objects.AddObjectTypesToQuery(ECC_Pawn);
    FCollisionQueryParams Query(SCENE_QUERY_STAT(PlaygroundPunch), false, this);
    TArray<FHitResult> Hits;
    GetWorld()->SweepMultiByObjectType(Hits, Start, End, FQuat::Identity, Objects,
        FCollisionShape::MakeSphere(bUltimate ? 155.f : (ActiveAttack == 6 || ActiveAttack == 7 ? 110.f : 78.f)), Query);
    TSet<AActor*> Damaged;
    const float DamageValues[] = {15.f, 20.f, 30.f, 40.f, 12.f, 100.f, 45.f, 65.f};
    const float FlurryDamage[] = {12.f, 12.f, 14.f, 16.f, 36.f};
    const float StrikeDamage = ActiveAttack == 4 ? FlurryDamage[FMath::Clamp(FlurryHit,0,4)] : DamageValues[ActiveAttack];
    bool bAnyHit = false;
    FVector UltimateContact = GetActorLocation() + GetActorForwardVector() * 145.f;
    float NearestContactDistance = TNumericLimits<float>::Max();
    for (const FHitResult& Hit : Hits)
    {
        APlaygroundTarget* Target = Cast<APlaygroundTarget>(Hit.GetActor());
        if (!Target || Damaged.Contains(Target) || !HasClearCombatPath(Target)) continue;
        if (FVector::DotProduct((Target->GetActorLocation()-GetActorLocation()).GetSafeNormal2D(),GetActorForwardVector()) < -.05f) continue;
        Damaged.Add(Target);
        // 피격 모션/회전이 바뀌기 전에 현재 몸 표면을 잡는다.
        FName ContactBone;
        const FVector Contact = Target->GetCombatContact(StrikePoint, GetActorLocation(), ContactBone);
        const float Applied = UGameplayStatics::ApplyDamage(Target, StrikeDamage, Controller, this, nullptr);
        if (Applied > 0.f)
        {
            bAnyHit = true;
            ++HitCount;
            if (!bUltimate)
            {
                UltimateCharge = FMath::Min(100.f, UltimateCharge + 100.f / 7.f);
                if (UltimateCharge > 99.99f) UltimateCharge = 100.f;
            }
            const float HitNow = GetWorld()->GetTimeSeconds();
            if (HitNow-LastHitTime > 2.2f) ComboHitCount = 0;
            ++ComboHitCount;
            LastHitTime = HitNow;
            LastContactBone = ContactBone;
            LastContactPoint = Contact;
            const float ContactDistance = FVector::DistSquared(Contact, GetActorLocation());
            if (ContactDistance < NearestContactDistance)
            {
                UltimateContact = Contact;
                NearestContactDistance = ContactDistance;
            }
            if (!bUltimate)
            {
                CombatPresentation->PlayCue(ImpactVariant >= 2 ? EComicEffect::HeavyImpact : EComicEffect::Impact,
                    Contact, ImpactVariant, (Target->GetActorLocation() - GetActorLocation()).GetSafeNormal2D());
            }
            if (APlayerController* PC = Cast<APlayerController>(Controller))
            {
                if (APlaygroundHUD* HUD = Cast<APlaygroundHUD>(PC->GetHUD()))
                    HUD->AddDamageNumber(Contact + FVector(0.f, 0.f, 55.f), Applied, ImpactVariant >= 2);
            }
        }
    }
    if (bUltimate && bAnyHit)
    {
        CombatPresentation->PlayCue(EComicEffect::UltimateImpact, UltimateContact, ActiveAttack, (UltimateContact - GetActorLocation()).GetSafeNormal2D());
    }
    if (bAnyHit)
    {
        CombatPresentation->ConfirmHit(ImpactVariant, UltimateContact, ComboHitCount > 0 && ComboHitCount / 6 > (ComboHitCount-Damaged.Num()) / 6);
        if (UComicSteppedMeshComponent* Stepped = Cast<UComicSteppedMeshComponent>(GetMesh())) Stepped->ResetPoseCadence();
        GetCharacterMovement()->StopMovementImmediately();
        DashUntil = -1.f;
        PreviousAnimRate = GetMesh()->GlobalAnimRateScale;
        GetMesh()->GlobalAnimRateScale = 0.f;
        PoseHoldUntil = GetWorld()->GetTimeSeconds() + (bUltimate ? .055f : ActiveAttack == 7 ? .035f : IsFlurryTap() ? .025f : ImpactVariant >= 2 ? .085f : .045f);
    }
}

void APlaygroundCharacter::RestorePoseRate()
{
    if (PoseHoldUntil >= 0.f) GetMesh()->GlobalAnimRateScale = PreviousAnimRate;
    PoseHoldUntil = -1.f;
}

void APlaygroundCharacter::OnAttackEnded(UAnimMontage* Montage, bool bInterrupted)
{
    if (Montage == ActiveMontage) FinishAttack();
}

void APlaygroundCharacter::FinishAttack()
{
    RestorePoseRate();
    bAttacking = false;
    AttackPhase = 0;
    bAwaitingLanding = false;
    bRisePending = false;
    GetMesh()->GlobalAnimRateScale = 1.f;
    ActiveMontage = nullptr;
    bCanChain = false;
    DashUntil = -1.f;
    AssistedTarget.Reset();
    LastComboEndTime = GetWorld()->GetTimeSeconds();
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->MaxWalkSpeed = bRunning ? SprintSpeed : JogSpeed;
}

void APlaygroundCharacter::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    RestorePoseRate();
    if (APlayerController* PC = Cast<APlayerController>(Controller))
    {
        if (PC->GetLocalPlayer() && Mapping)
            PC->GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>()->RemoveMappingContext(Mapping);
    }
    Super::EndPlay(EndPlayReason);
}

void APlaygroundCharacter::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const float Now = GetWorld()->GetTimeSeconds();
    if (Now-LastHitTime > 2.2f) ComboHitCount = 0;
    if (PoseHoldUntil >= 0.f && Now >= PoseHoldUntil) RestorePoseRate();
    if (bRisePending && PoseHoldUntil < 0.f)
    {
        bRisePending = false;
        LaunchCharacter(GetActorForwardVector()*110.f + FVector(0,0,560.f),true,true);
    }
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    // 정지 착지 도중 이동을 시작해도 즉시 이동 포즈로 돌아간다.
    if (MovementMontage && Anim && !GetCharacterMovement()->IsFalling()
        && GetVelocity().SizeSquared2D() > FMath::Square(120.f))
    {
        Anim->Montage_Stop(.10f, MovementMontage);
        MovementMontage = nullptr;
    }
    const float ClipTime = bAttacking && ActiveMontage && Anim ? Anim->Montage_GetPosition(ActiveMontage) : 0.f;
    AttackClipTime = ClipTime;
    const float ImpactTimes[] = {.1333f, .1833f, .2667f, .35f, .20f, .88f, .3167f, .25f};
    const float ImpactTime = ImpactTimes[FMath::Clamp(ActiveAttack, 0, 7)];
    DisplayPoseFPS = 0.f; // Evaluate animation every frame; hit-stop is independent.
    if (bAttacking && PoseHoldUntil <= Now)
    {
        if (ActiveAttack == 6 && GetCharacterMovement()->IsFalling() && ClipTime > .18f)
            GetCharacterMovement()->Velocity.Z = FMath::Min(GetCharacterMovement()->Velocity.Z, -1050.f);
        if (ActiveAttack < 4 && !GetCharacterMovement()->IsFalling())
        {
            const float Travel[] = {22.f, 30.f, 26.f, 34.f};
            const float Progress = FMath::SmoothStep(ImpactTime - .09f, ImpactTime + .025f, ClipTime);
            const float Advance = FMath::Max(0.f, Progress - LungeProgress) * Travel[ActiveAttack];
            LungeProgress = Progress;
            AddActorWorldOffset(GetActorForwardVector() * Advance, true);
        }
    }
    if (PoseHoldUntil > Now) GetCharacterMovement()->StopMovementImmediately();
    if (DashUntil > Now && PoseHoldUntil <= Now)
    {
        const float Z = GetCharacterMovement()->Velocity.Z;
        float RushSpeed = 2000.f;
        if (AssistedTarget.IsValid() && HasClearCombatPath(AssistedTarget.Get()))
        {
            const FVector Delta = AssistedTarget->GetActorLocation()-GetActorLocation();
            SetActorRotation(FMath::RInterpTo(GetActorRotation(),Delta.GetSafeNormal2D().Rotation(),DeltaSeconds,14.f));
            RushSpeed = FMath::Clamp((Delta.Size2D()-125.f)/FMath::Max(.03f,DashUntil-Now),0.f,2400.f);
        }
        GetCharacterMovement()->Velocity = GetActorForwardVector() * RushSpeed;
        GetCharacterMovement()->Velocity.Z = Z;
    }
    else if (DashUntil > 0.f)
    {
        DashUntil = -1.f;
        GetCharacterMovement()->MaxWalkSpeed = bRunning ? SprintSpeed : JogSpeed;
    }
    ConsumeBufferedAction();
    if (GetActorLocation().Z < -700.f)
    {
        if (Anim) Anim->StopAllMontages(.05f);
        FinishAttack();
        SetActorLocation(FVector(-650.f, 0.f, 110.f));
        GetCharacterMovement()->StopMovementImmediately();
    }
}

void APlaygroundCharacter::TogglePoseStep()
{
    bStylizedPoseStep = false;
}

void APlaygroundCharacter::SetAutomationInputIsolation(bool bEnabled)
{
#if WITH_EDITOR
    if (APlayerController* PC = Cast<APlayerController>(Controller))
    {
        // 자동 입력은 PC->InputKey로 전달한다. 뷰포트의 수동 입력만 검증 중에 분리한다.
        PC->FlushPressedKeys();
        MoveIntent = FVector::ZeroVector;
        LastMoveInputAt = -10.f;
        GetCharacterMovement()->StopMovementImmediately();
        if (bEnabled) PC->SetInputMode(FInputModeUIOnly());
        else PC->SetInputMode(FInputModeGameOnly());
    }
#endif
}

void APlaygroundCharacter::InjectControlKey(FName KeyName, bool bPressed)
{
    if (APlayerController* PC = Cast<APlayerController>(Controller))
    {
        PC->InputKey(FInputKeyEventArgs::CreateSimulated(FKey(KeyName), bPressed ? IE_Pressed : IE_Released, bPressed ? 1.f : 0.f));
    }
}

APlaygroundTarget::APlaygroundTarget()
{
    PrimaryActorTick.bCanEverTick = true;
    Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TargetBody"));
    RootComponent = Body;
    // 기존 맵의 TargetBody 서브오브젝트 이름은 보존하고 시각/충돌을 분리한다.
    Body->SetCollisionProfileName(TEXT("NoCollision"));
    TargetCollision = CreateDefaultSubobject<UCapsuleComponent>(TEXT("TargetCollision"));
    TargetCollision->SetupAttachment(RootComponent);
    TargetCollision->InitCapsuleSize(42.f, 96.f);
    TargetCollision->SetCollisionProfileName(TEXT("BlockAllDynamic"));
    TargetCollision->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
    CharacterVisual = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("CharacterVisual"));
    CharacterVisual->SetupAttachment(RootComponent);
    CharacterVisual->SetRelativeLocation(FVector(0.f, 0.f, -96.f));
    CharacterVisual->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));
    CharacterVisual->SetCollisionProfileName(TEXT("NoCollision"));
    CharacterVisual->SetRenderCustomDepth(true);
    CharacterVisual->SetCustomDepthStencilValue(12);
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> Manny(TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"));
    CharacterVisual->SetSkeletalMesh(Manny.Object);
    static ConstructorHelpers::FObjectFinder<UAnimSequence> Idle(TEXT("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle.MM_Idle"));
    IdleAnimation = Idle.Object;
    const TCHAR* HitNames[] = {TEXT("Left"), TEXT("Right"), TEXT("Heavy"), TEXT("Ultimate")};
    for (const TCHAR* Name : HitNames)
    {
        const FString Path = FString::Printf(TEXT("/Game/ComicCombat/Animations/A_CC_TargetHit%s.A_CC_TargetHit%s"), Name, Name);
        ConstructorHelpers::FObjectFinder<UAnimSequence> Hit(*Path);
        HitAnimations.Add(Hit.Object);
    }
    Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("HealthLabel"));
    Label->SetupAttachment(RootComponent);
    Label->SetAbsolute(false, true, true);
    Label->SetRelativeLocation(FVector(0.f, 0.f, 115.f));
    Label->SetWorldSize(13.f);
    Label->SetHorizontalAlignment(EHorizTextAligment::EHTA_Center);
    Label->SetTextRenderColor(FColor(195, 166, 205));
}

void APlaygroundTarget::BeginPlay()
{
    Super::BeginPlay();
    Body->SetStaticMesh(nullptr);
    Body->SetCollisionProfileName(TEXT("NoCollision"));
    Body->SetRenderCustomDepth(false);
    SetActorScale3D(FVector::OneVector);
    FVector Position = GetActorLocation();
    Position.Z = 96.f;
    SetActorLocation(Position);
    SetActorRotation(FRotator(0.f, 180.f, 0.f));
    if (UMaterialInterface* Armor = LoadObject<UMaterialInterface>(nullptr,
        TEXT("/Game/ComicCombat/Materials/M_CC_Armor.M_CC_Armor")))
    {
        BodyMaterial = UMaterialInstanceDynamic::Create(Armor, this);
        BodyMaterial->SetVectorParameterValue(TEXT("Color"), FLinearColor(.68f, .025f, .09f));
        CharacterVisual->SetMaterial(0, BodyMaterial);
        TrimMaterial = UMaterialInstanceDynamic::Create(Armor, this);
        TrimMaterial->SetVectorParameterValue(TEXT("Color"), FLinearColor(.13f, .035f, .17f));
        CharacterVisual->SetMaterial(1, TrimMaterial);
    }
    CharacterVisual->PlayAnimation(IdleAnimation, true);
    RestLocation = GetActorLocation();
    UpdateLabel();
}

void APlaygroundTarget::UpdateLabel()
{
    Label->SetText(FText::FromString(TEXT("TRAINING  /  IMMORTAL")));
}

float APlaygroundTarget::TakeDamage(float Damage, const FDamageEvent& Event, AController* EventInstigator, AActor* Causer)
{
    if (!FMath::IsFinite(Damage) || Damage <= 0.f) return 0.f;
    // 연습 대상은 체력을 소진하지 않는다. 실제 요청된 양을 피격 숫자로 돌려준다.
    Health = 100.f;
    const float Applied = Damage;
    ++HitsReceived;
    const APlaygroundCharacter* Attacker = Cast<APlaygroundCharacter>(Causer);
    const int32 Variant = Attacker ? Attacker->GetImpactVariant() : Damage >= 100.f ? 5 : Damage >= 30.f ? 3 : 0;
    const int32 Reaction = Variant == 5 ? 3 : Variant >= 2 ? 2 : Variant % 2;
    UAnimSequence* Clip = HitAnimations.IsValidIndex(Reaction) ? HitAnimations[Reaction].Get() : nullptr;
    ReactionHold = Attacker && Attacker->IsFlurryTap() ? .025f : Variant == 7 ? .035f : Reaction == 3 ? .055f : Reaction == 2 ? .085f : .045f;
    ReactionDuration = (Clip ? Clip->GetPlayLength() : .5f) + ReactionHold;
    ReactionTime = ReactionDuration;
    ReactionDistance = Attacker && Attacker->IsFlurryTap() ? 8.f : Reaction == 3 ? 130.f : Reaction == 2 ? 62.f : 23.f;
    if (Variant == 7) { ReactionDuration = 1.15f; ReactionTime = ReactionDuration; ReactionDistance = 75.f; }
    ReactionLift = Variant == 7 ? 260.f : Variant == 2 ? 55.f : Reaction == 3 ? 85.f : Reaction == 2 ? 16.f : 3.f;
    PoseHoldRemaining = ReactionHold;
    FlashDuration = Reaction == 3 ? .12f : Reaction == 2 ? .10f : .075f;
    FlashTime = FlashDuration;
    ReactionStart = GetActorLocation();
    ReactionDirection = Causer ? (ReactionStart - Causer->GetActorLocation()).GetSafeNormal2D() : FVector::ForwardVector;
    if (!ReactionDirection.IsNearlyZero()) SetActorRotation((-ReactionDirection).Rotation());
    CharacterVisual->PlayAnimation(Clip ? Clip : IdleAnimation.Get(), false);
    CharacterVisual->SetPosition(0.f, false);
    CharacterVisual->GlobalAnimRateScale = 0.f;
    if (UComicSteppedMeshComponent* Stepped = Cast<UComicSteppedMeshComponent>(CharacterVisual))
    {
        Stepped->ResetPoseCadence();
        Stepped->SetPoseCadence(60.f);
    }
    HitAnimationTime = ReactionDuration;
    UpdateLabel();
    return Applied;
}

FVector APlaygroundTarget::GetCombatContact(const FVector& StrikePoint, const FVector& AttackerLocation, FName& Bone) const
{
    const FVector Outward = (AttackerLocation - GetActorLocation()).GetSafeNormal2D();
    // 관대한 판정으로 주먹이 몸 안/뒤에 들어간 경우에도 공격자 쪽 표면을 선택한다.
    FVector Probe = StrikePoint;
    const float Front = FVector::DotProduct(Probe - GetActorLocation(), Outward);
    Probe += Outward * FMath::Max(0.f, TargetCollision->GetScaledCapsuleRadius() + 5.f - Front);
    FVector Point, Normal;
    float Distance = 0.f;
    if (CharacterVisual && CharacterVisual->K2_GetClosestPointOnPhysicsAsset(Probe, Point, Normal, Bone, Distance))
    {
        return Point + Normal.GetSafeNormal() * 2.f;
    }
    Bone = NAME_None;
    FVector Fallback = GetActorLocation() + Outward * (TargetCollision->GetScaledCapsuleRadius() + 2.f);
    Fallback.Z = FMath::Clamp(StrikePoint.Z, GetActorLocation().Z - 60.f, GetActorLocation().Z + 65.f);
    return Fallback;
}

void APlaygroundTarget::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    FlashTime = FMath::Max(0.f, FlashTime - DeltaSeconds);
    if (PoseHoldRemaining > 0.f)
    {
        PoseHoldRemaining = FMath::Max(0.f, PoseHoldRemaining - DeltaSeconds);
        if (PoseHoldRemaining <= 0.f) CharacterVisual->GlobalAnimRateScale = 1.f;
    }
    if (UComicSteppedMeshComponent* Stepped = Cast<UComicSteppedMeshComponent>(CharacterVisual))
        Stepped->SetPoseCadence(ReactionTime > ReactionDuration - .18f ? 60.f : 18.f);
    Label->SetVisibility(false);
    if (ReactionTime > 0.f)
    {
        ReactionTime = FMath::Max(0.f, ReactionTime - DeltaSeconds);
        const float Age = ReactionDuration - ReactionTime;
        // 몸이 먼저 꺾인 뒤 밀리고, 회복 동작 후반에 제자리로 돌아온다. 연타는 현재 위치에서 이어진다.
        const float Push = FMath::Clamp((Age - ReactionHold) / .12f, 0.f, 1.f);
        const float Return = FMath::Clamp((Age - ReactionDuration * .42f) / (ReactionDuration * .58f), 0.f, 1.f);
        const FVector Pushed = ReactionStart + ReactionDirection * ReactionDistance * (1.f - FMath::Pow(1.f - Push, 3.f));
        FVector Position = FMath::Lerp(Pushed, RestLocation, Return * Return * (3.f - 2.f * Return));
        const float Flight = FMath::Clamp((Age - ReactionHold) / (ReactionDuration - ReactionHold), 0.f, 1.f);
        Position.Z += ReactionLift * FMath::Sin(Flight * UE_PI);
        SetActorLocation(Position);
    }
    if (HitAnimationTime > 0.f)
    {
        HitAnimationTime = FMath::Max(0.f, HitAnimationTime - DeltaSeconds);
        if (HitAnimationTime <= 0.f) CharacterVisual->PlayAnimation(IdleAnimation, true);
    }
    if (BodyMaterial)
    {
        const float Flash = FMath::Square(FMath::Clamp(FlashTime / FlashDuration, 0.f, 1.f));
        BodyMaterial->SetScalarParameterValue(TEXT("HitFlash"), Flash);
        if (TrimMaterial) TrimMaterial->SetScalarParameterValue(TEXT("HitFlash"), Flash);
    }
    if (APlayerCameraManager* Camera = UGameplayStatics::GetPlayerCameraManager(this, 0))
        Label->SetWorldRotation((Camera->GetCameraLocation() - Label->GetComponentLocation()).Rotation());
}

APlaygroundHUD::APlaygroundHUD()
{
    PrimaryActorTick.bCanEverTick = true;
    static ConstructorHelpers::FObjectFinder<UFont> Font(TEXT("/Engine/EngineFonts/RobotoDistanceField.RobotoDistanceField"));
    DamageFont = Font.Object;
    static ConstructorHelpers::FObjectFinder<UTexture2D> PortraitAsset(TEXT("/Game/ComicCombat/UI/T_PlayerPortrait.T_PlayerPortrait"));
    static ConstructorHelpers::FObjectFinder<UFontFace> DisplayAsset(TEXT("/Game/ComicCombat/UI/FF_HUD_Impact.FF_HUD_Impact"));
    static ConstructorHelpers::FObjectFinder<UFontFace> BodyAsset(TEXT("/Game/ComicCombat/UI/FF_HUD_Malgun.FF_HUD_Malgun"));
    static ConstructorHelpers::FObjectFinder<UFontFace> BoldAsset(TEXT("/Game/ComicCombat/UI/FF_HUD_MalgunBold.FF_HUD_MalgunBold"));
    static ConstructorHelpers::FObjectFinder<UFontFace> LatinAsset(TEXT("/Game/ComicCombat/UI/FF_HUD_Arial.FF_HUD_Arial"));
    static ConstructorHelpers::FObjectFinder<UFontFace> LatinBoldAsset(TEXT("/Game/ComicCombat/UI/FF_HUD_ArialBold.FF_HUD_ArialBold"));
    static ConstructorHelpers::FObjectFinder<UFontFace> ItalicAsset(TEXT("/Game/ComicCombat/UI/FF_HUD_ArialBoldItalic.FF_HUD_ArialBoldItalic"));
    Portrait=PortraitAsset.Object;
    HudDisplayFace=DisplayAsset.Object;
    HudBodyFace=BodyAsset.Object;
    HudBodyBoldFace=BoldAsset.Object;HudLatinFace=LatinAsset.Object;
    HudLatinBoldFace=LatinBoldAsset.Object;HudLatinItalicFace=ItalicAsset.Object;
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> ComboAsset(TEXT("/Game/ComicCombat/UI/M_ComboBackplate.M_ComboBackplate"));
    ComboBackdropBase=ComboAsset.Object;
}

void APlaygroundHUD::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    // 창이 가려져 DrawHUD가 생략돼도 표시 데이터는 게임 시간에 맞춰 소멸한다.
    const float Now = GetWorld()->GetTimeSeconds();
    DamageNumbers.RemoveAll([Now](const FDamageNumber& Number) { return Now - Number.SpawnTime > (Number.bFinisher ? .85f : .60f); });
}

void APlaygroundHUD::DrawHUD()
{
    Super::DrawHUD();
    APlaygroundCharacter* Player = Cast<APlaygroundCharacter>(GetOwningPawn());
    if (!Canvas || !Player) return;
    if (const UComicCombatPresentationComponent* Presentation = Player->FindComponentByClass<UComicCombatPresentationComponent>())
        if (Presentation->IsImpactFlashActive()) return;
    DrawCombatInterface(Player);
    const float Scale = FMath::Clamp(Canvas->SizeX / 1280.f, .75f, 1.5f);
    const float Now = GetWorld()->GetTimeSeconds();
    for (const FDamageNumber& Number : DamageNumbers)
    {
        const float Age = Now - Number.SpawnTime;
        // 현재 HUD 캔버스의 투영을 사용한다. PIE/고해상도 캡처의 뷰포트 크기 차이를 피한다.
        const FVector Projected = Canvas->Project(Number.Location);
        if (Projected.Z <= 0.f) continue;
        FVector2D Screen(Projected.X, Projected.Y);
        const FString Digits = FString::FromInt(FMath::RoundToInt(Number.Damage));
        UFont* NumberFont = DamageFont ? DamageFont.Get() : GEngine->GetLargeFont();
        const float UnitScale = Scale * (Number.bFinisher ? 2.f : Number.Damage <= 20.f ? 1.25f : 1.55f);
        float GlyphWidth = 0.f, GlyphHeight = 0.f;
        Canvas->StrLen(NumberFont, TEXT("0"), GlyphWidth, GlyphHeight);
        const float Spacing = GlyphWidth * UnitScale * .98f;
        Screen.X += Number.Side * (26.f + 48.f * (1.f - FMath::Exp(-Age * 5.f))) * Scale;
        Screen.Y -= (10.f + 100.f * (1.f - FMath::Exp(-Age * 5.f))) * Scale;
        const float Alpha = FMath::Clamp(((Number.bFinisher ? .85f : .60f) - Age) / .18f, 0.f, 1.f);
        for (int32 I = 0; I < Digits.Len(); ++I)
        {
            const float DigitAge = Age - I * .025f;
            if (DigitAge < 0.f) continue;
            const float Bounce = FMath::Exp(-DigitAge * 13.f) * FMath::Sin(DigitAge * 27.f);
            const float Pop = .82f + .18f * FMath::Min(1.f, DigitAge / .06f) + Bounce * .58f;
            const float Angle = Number.Side * (8.f * FMath::Exp(-DigitAge * 10.f) + 2.f);
            const FVector2D Origin(Screen.X + (I - (Digits.Len() - 1) * .5f) * Spacing,
                Screen.Y - Bounce * 15.f * Scale - (I % 2) * 4.f * Scale);
            Canvas->Canvas->PushRelativeTransform(FRotationMatrix(FRotator(0.f, Angle, 0.f))
                * FTranslationMatrix(FVector(Origin.X, Origin.Y, 0.f)));
            const float TextScale = UnitScale * Pop;
            const FText Digit = FText::FromString(Digits.Mid(I, 1));
            // 두꺼운 잉크 그림자와 숫자별 스냅/튕김. 타격점에서 바깥 위쪽으로 분리한다.
            for (int32 J = 0; J < 5; ++J)
            {
                const FVector2D Offsets[] = {FVector2D(-2,-2),FVector2D(2,-2),FVector2D(-2,2),FVector2D(3,4),FVector2D(0,0)};
                const FLinearColor Color = J == 4
                    ? FLinearColor(1.f, Number.bFinisher ? .63f : .83f, .17f, Alpha)
                    : FLinearColor(.012f, .009f, .025f, Alpha);
                FCanvasTextItem Text(Offsets[J] * Scale, Digit, NumberFont, Color);
                Text.Scale = FVector2D(TextScale);
                Text.bCentreX = true;
                Text.bCentreY = true;
                Canvas->DrawItem(Text);
            }
            Canvas->Canvas->PopTransform();
        }
    }
}

void APlaygroundHUD::AddDamageNumber(const FVector& Location, float Damage, bool bFinisher)
{
    if (DamageNumbers.Num() >= 32) DamageNumbers.RemoveAt(0);
    const float Side = DamageNumbers.Num() % 2 == 0 ? -1.f : 1.f;
    DamageNumbers.Add({Location, Damage, GetWorld()->GetTimeSeconds(), Side, bFinisher});
}

APlaygroundGameMode::APlaygroundGameMode()
{
    DefaultPawnClass = APlaygroundCharacter::StaticClass();
    HUDClass = APlaygroundHUD::StaticClass();
    PlayerControllerClass = ACombatPlayerController::StaticClass();
}
