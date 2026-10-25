#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "GameFramework/PlayerController.h"
#include "Playground.generated.h"

class APlaygroundTarget;
class UCameraComponent;
class UFont;
class USpringArmComponent;
class UInputAction;
class UInputMappingContext;
class UAnimSequence;
class UAnimSequenceBase;
class UStaticMeshComponent;
class UCapsuleComponent;
class USkeletalMeshComponent;
class UTextRenderComponent;
class UMaterialInstanceDynamic;
class UAnimMontage;
class UComicCombatPresentationComponent;
class UFontFace;
class UTexture2D;
struct FCompositeFont;
struct FInputActionValue;

UCLASS()
class TEST_API APlaygroundCharacter : public ACharacter
{
    GENERATED_BODY()
public:
    APlaygroundCharacter(const FObjectInitializer& ObjectInitializer = FObjectInitializer::Get());
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void PawnClientRestart() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void OnJumped_Implementation() override;
    virtual void Landed(const FHitResult& Hit) override;
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Controls") bool bRunning = false;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") bool bAttacking = false;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") int32 AttackCount = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") int32 HitCount = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") float LastHitTime = -10.f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Presentation") bool bStylizedPoseStep = true;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Presentation") float DisplayPoseFPS = 18.f;

    // Routes verification events through the real PlayerController + Enhanced Input mapping.
    UFUNCTION(BlueprintCallable, Category="Verification", meta=(DevelopmentOnly))
    void InjectControlKey(FName KeyName, bool bPressed);
    /** 에디터 자동 검증 동안 수동 뷰포트 입력만 분리한다. 종료 시 반드시 복원한다. */
    UFUNCTION(BlueprintCallable, Category="Verification", meta=(DevelopmentOnly))
    void SetAutomationInputIsolation(bool bEnabled);


    /** 클립 노티파이 전용. 진행 중인 공격에서 각 타격은 한 번만 판정한다. */
    void HandleCombatCue(int32 Cue, UAnimSequenceBase* SourceAnimation);
    /** 호환용 조회. 궁극기는 재사용 대기 없이 항상 0초를 반환한다. */
    UFUNCTION(BlueprintPure, Category="Combat")
    float GetUltimateCooldown() const;
    UFUNCTION(BlueprintPure, Category="Combat")
    float GetFlurryCooldown() const;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Vitals") float Health = 1000.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Vitals") float MaxHealth = 1000.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") float UltimateCharge = 0.f;
    virtual float TakeDamage(float Damage, const FDamageEvent& Event, AController* EventInstigator, AActor* Causer) override;
    UFUNCTION(BlueprintPure, Category="Combat")
    int32 GetAttackVariant() const { return ActiveAttack; }
    int32 GetImpactVariant() const { return ActiveAttack == 4 ? (FlurryHit < 4 ? FlurryHit % 2 : 2) : ActiveAttack; }
    bool IsFlurryTap() const { return ActiveAttack == 4 && FlurryHit < 4; }
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") int32 ComboHitCount = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") int32 CancelCount = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") int32 LightChain = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") FVector LastContactPoint = FVector::ZeroVector;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") int32 AttackPhase = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Combat") float AttackClipTime = 0.f;

private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USpringArmComponent> CameraBoom;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UCameraComponent> FollowCamera;
    UPROPERTY() TObjectPtr<UInputMappingContext> Mapping;
    UPROPERTY() TObjectPtr<UInputAction> MoveAction;
    UPROPERTY() TObjectPtr<UInputAction> LookAction;
    UPROPERTY() TObjectPtr<UInputAction> JumpAction;
    UPROPERTY() TObjectPtr<UInputAction> AttackAction;
    UPROPERTY() TObjectPtr<UInputAction> RunAction;
    UPROPERTY() TObjectPtr<UInputAction> HeavyAction;
    UPROPERTY() TObjectPtr<UInputAction> DashAction;
    UPROPERTY() TObjectPtr<UInputAction> UltimateAction;
    UPROPERTY() TObjectPtr<UInputAction> PoseStepAction;
    UPROPERTY() TObjectPtr<UInputAction> CancelAction;
    UPROPERTY() TArray<TObjectPtr<UAnimSequence>> AttackAnimations;
    UPROPERTY() TArray<TObjectPtr<UAnimSequence>> MovementAnimations;
    UPROPERTY() TObjectPtr<UAnimMontage> ActiveMontage;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UComicCombatPresentationComponent> CombatPresentation;
    float ChainBlendUntil = -1.f;
    bool bContinuousAttack = false;
    float LastAttackTime = -10.f;
    float LastComboEndTime = -10.f;
    float BufferedUntil = -1.f;
    float PoseHoldUntil = -1.f;
    int32 BufferedAction = -1;
    float LastMoveInputAt = -10.f;
    FVector MoveIntent = FVector::ZeroVector;
    TWeakObjectPtr<APlaygroundTarget> AssistedTarget;
    bool bStartingLight = false;
    void RequestAction(int32 Action);
    void ConsumeBufferedAction();
    void CancelAttack();
    APlaygroundTarget* FindAssistedTarget(const FVector& Direction, float Range, float MinDot) const;
    bool HasClearCombatPath(const APlaygroundTarget* Target) const;
    float DashReadyAt = 0.f;
    float DashUntil = -1.f;
    float PreviousAnimRate = 1.f;
    int32 FlurryHit = -1;
    int32 ComboIndex = 0;
    int32 ActiveAttack = 0;
    bool bCanChain = false;
    bool bStrikeResolved = false;
    bool bAwaitingLanding = false;
    bool bRisePending = false;
    float LungeProgress = 0.f;
    void TogglePoseStep();
    void Move(const FInputActionValue& Value);
    void Look(const FInputActionValue& Value);
    void StartRun();
    void StopRun();
    void Attack();
    void HeavyAttack();
    void DashAttack();
    void UltimateAttack();
    void JumpPressed();
    void PlayMovementAnimation(int32 Index);
    void StartAttack(int32 Variant);
    void OnAttackEnded(UAnimMontage* Montage, bool bInterrupted);
    void RestorePoseRate();
    void ResolveAttack();
    void FinishAttack();
};

UCLASS()
class TEST_API APlaygroundTarget : public AActor
{
    GENERATED_BODY()
public:
    APlaygroundTarget();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual float TakeDamage(float Damage, const FDamageEvent& Event, AController* EventInstigator, AActor* Causer) override;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Target") float Health = 100.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Target") int32 HitsReceived = 0;
    /** 몸 표면의 접촉점을 반환한다. 타격 연출이 몸 안에 묻히지 않도록 여유 거리를 포함한다. */
    FVector GetCombatContact(const FVector& AttackerLocation, int32 Variant) const;
private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Body;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UCapsuleComponent> TargetCollision;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USkeletalMeshComponent> CharacterVisual;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UTextRenderComponent> Label;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> BodyMaterial;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> TrimMaterial;
    UPROPERTY() TObjectPtr<UAnimSequence> IdleAnimation;
    UPROPERTY() TArray<TObjectPtr<UAnimSequence>> HitAnimations;
    float FlashTime = 0.f;
    float HitAnimationTime = 0.f;
    FVector RestLocation = FVector::ZeroVector;
    FVector ReactionDirection = FVector::ForwardVector;
    float ReactionTime = 0.f;
    float ReactionDuration = .43f;
    float ReactionDistance = 10.f;
    float ReactionHold = .05f;
    float FlashDuration = .08f;
    float PoseHoldRemaining = 0.f;
    float ReactionLift = 0.f;
    FVector ReactionStart = FVector::ZeroVector;
    void UpdateLabel();
};

UCLASS()
class TEST_API APlaygroundHUD : public AHUD
{
    GENERATED_BODY()
public:
    APlaygroundHUD();
    virtual void Tick(float DeltaSeconds) override;
    virtual void DrawHUD() override;
    void DrawCombatInterface(APlaygroundCharacter* Player);
    bool HandleInterfaceClick(const FVector2D& Position);
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="HUD") bool bDebugVisible = false;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="HUD") int32 HudComboCount = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="HUD") float HudComboRemaining = 0.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="HUD") float DisplayHealth = 1000.f;
    /** 성공한 피해량만 표시한다. 위치는 명중 시 월드 좌표이며 카메라를 따라 투영한다. */
    void AddDamageNumber(const FVector& Location, float Damage, bool bFinisher);
    /** 현재 화면 표시 수. 전투 연출 검증에서 수명과 정리를 확인한다. */
    UFUNCTION(BlueprintPure, Category="Verification", meta=(DevelopmentOnly))
    int32 GetActiveDamageNumberCount() const { return DamageNumbers.Num(); }
private:
    UPROPERTY() TObjectPtr<UFont> DamageFont;
    UPROPERTY() TObjectPtr<UTexture2D> Portrait;
    UPROPERTY() TObjectPtr<UFontFace> HudDisplayFace;
    UPROPERTY() TObjectPtr<UFontFace> HudBodyFace;
    UPROPERTY() TObjectPtr<UFontFace> HudBodyBoldFace;
    UPROPERTY() TObjectPtr<UFontFace> HudLatinFace;
    UPROPERTY() TObjectPtr<UFontFace> HudLatinBoldFace;
    UPROPERTY() TObjectPtr<UFontFace> HudLatinItalicFace;
    UPROPERTY() TObjectPtr<UFont> HudDisplayFont;
    UPROPERTY() TObjectPtr<UFont> HudBodyFont;
    UPROPERTY() TObjectPtr<UFont> HudBoldFont;
    UPROPERTY() TObjectPtr<UFont> HudItalicFont;
    float DisplayUltimate = 0.f;
    UPROPERTY() TObjectPtr<UMaterialInterface> ComboBackdropBase;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> ComboBackdropMaterial;
    float HudComboStarted = -10.f;
    int32 HudTintIndex = -1;
    int32 HudObservedHits = 0;
    float HudLastHit = -10.f;
    float HudLastDamage = -10.f;
    float HudPreviousHealth = 1000.f;
    float HudPreviousFrame = -1.f;
    float HudLastAttack = -10.f;
    int32 HudObservedAttacks = 0;
    float HudUnit = 1.f;
    TMap<FName,FBox2D> InterfaceRegions;
    struct FDamageNumber
    {
        FVector Location;
        float Damage;
        double SpawnTime;
        float Side;
        bool bFinisher;
    };
    TArray<FDamageNumber> DamageNumbers;
};

UCLASS()
class TEST_API ACombatPlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual bool InputKey(const FInputKeyEventArgs& Params) override;
    UFUNCTION(BlueprintCallable, Category="HUD") void SetCombatPaused(bool bPaused);
};

UCLASS()
class TEST_API APlaygroundGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    APlaygroundGameMode();
};
