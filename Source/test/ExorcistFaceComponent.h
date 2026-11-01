#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ExorcistFaceComponent.generated.h"

class USkeletalMeshComponent;
class UAnimInstance;
class APlaygroundCharacter;

/** 전투 진행 시간에 맞춰 기존 얼굴 모프를 혼합한다. 음성 립싱크는 별도 시스템이다. */
UCLASS(ClassGroup=(Presentation), meta=(BlueprintSpawnableComponent))
class TEST_API UExorcistFaceComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UExorcistFaceComponent();
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType,
        FActorComponentTickFunction* ThisTickFunction) override;
    /** EXORCIST와 기존 마네킹의 서로 다른 뼈 이름을 연결한다. */
    static FVector AttachmentLocation(USkeletalMeshComponent* Mesh, FName LegacyName);
    /** 공격별 접촉 부위. 발차기는 오른발, 잽/연타 준비는 왼손, 나머지는 오른손이다. */
    static FVector StrikeLocation(USkeletalMeshComponent* Mesh, int32 Variant);
    static FVector StrikeBaseLocation(USkeletalMeshComponent* Mesh, int32 Variant);
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float ExpressionIntensity = 0.f;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly) float MouthOpen = 0.f;
private:
    UPROPERTY() TObjectPtr<APlaygroundCharacter> Player;
    float FaceClock = 0.f;
    float LastHealth = 1000.f;
    float HurtUntil = -1.f;
    float Blink = 0.f;
    float IdleTime = 0.f;
    UPROPERTY(VisibleAnywhere, Category="Verification") float ClothPhysicsWeight = 0.f;
    float AppliedClothWeight = -1.f;
    TWeakObjectPtr<UAnimInstance> ClothAnimInstance;
    float NextBlink = 2.3f;
    float BlinkStart = -10.f;
    int32 BlinkIndex = 0;
    UPROPERTY(VisibleAnywhere, Category="Verification") int32 IdleExpression = 0;
    UPROPERTY(VisibleAnywhere, Category="Verification") float IdleExpressionWeight = 0.f;
};
