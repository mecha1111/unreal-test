#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ComicCombatEffect.h"
#include "ComicCombatPresentationComponent.generated.h"

class UCameraComponent;
class USpringArmComponent;
class UMaterialInstanceDynamic;
class UPointLightComponent;
class USoundBase;

/** 로컬 전투 카메라와 VFX만 담당한다. 체력/공격 상태는 캐릭터가 소유한다. */
UCLASS()
class TEST_API UComicCombatPresentationComponent : public UActorComponent
{
	GENERATED_BODY()
public:
	UComicCombatPresentationComponent();
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;
	/** 카메라 설정을 시작 값으로 저장한다. 소유 캐릭터 BeginPlay에서 호출한다. */
	void BindCamera(UCameraComponent* InCamera, USpringArmComponent* InBoom);
	void PlayCue(EComicEffect Effect, const FVector& Location, int32 Variant);
	void ConfirmHit(int32 Variant, const FVector& Contact, bool bComboFinish = false);
	/** 취소/종료 시 이 컴포넌트가 적용한 시간 배율과 화면 연출을 복구한다. */
	void CancelPresentation();
	void BeginAttack(int32 Variant);
	/** 실제 점프 성공/착지 때 호출한다. 카메라와 발밑 VFX만 갱신한다. */
	void OnJump(bool bAirJump);
	void OnLanding(float DownwardSpeed, const FVector& GroundPoint);
	/** 궁극기 임팩트 프레임 동안 HUD도 숨겨 전체 화면 대비를 유지한다. */
	bool IsImpactFlashActive() const { return UltimateFlashAge < FlashDuration; }
private:
	UPROPERTY() TObjectPtr<UCameraComponent> Camera;
	UPROPERTY() TObjectPtr<USpringArmComponent> Boom;
	UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> ComicMaterial;
	UPROPERTY() TObjectPtr<UPointLightComponent> ImpactLight;
	UPROPERTY() TArray<TObjectPtr<USoundBase>> ImpactSounds;
	UPROPERTY() TObjectPtr<USoundBase> WhooshSound;
	// 소유 캐릭터의 수명 안에서만 보관한다. 초과 재생은 일회성 액터로 처리한다.
	UPROPERTY(Transient) TArray<TObjectPtr<AComicCombatEffect>> EffectPool;
	static constexpr int32 MaxRetainedEffects = 16;
	FVector BaseOffset = FVector::ZeroVector;
	float BaseFov = 85.f;
	float BaseArmLength = 420.f;
	float AttackAge = 10.f;
	float FramingWeight = 0.f;
	int32 FramingVariant = 0;
	float KickAge = 1.f;
	float KickStrength = 0.f;
	float FootPreviousHeight[2] = {0.f,0.f};
    bool FootArmed[2] = {false,false};
    float FootLastSpawn[2] = {-10.f,-10.f};
    UPROPERTY(VisibleAnywhere, Category="Verification") int32 FootPlantCount = 0;
    UPROPERTY(VisibleAnywhere, Category="Verification") FVector LastFootPlant = FVector::ZeroVector;
    float FlashDuration = .15f;
    float SlowEndRealTime = -1.f;
    float PreviousTimeDilation = 1.f;
    void RestoreTimeDilation();
	float UltimateFlashAge = 1.f;
	float JumpAge = 2.f;
	float LandingAge = 2.f;
	float LandingStrength = 0.f;
	float SmoothedRun = 0.f;
	float AirPitch = 0.f;
	float AirOffset = 0.f;
	float StridePhase = 0.f;
	float HitSide = 1.f;
	int32 FootstepIndex = 0;
	FVector PreviousLocation = FVector::ZeroVector;
};
