#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CombatAuthoringLibrary.generated.h"
class UBlendSpace;
class USkeletalMeshComponent;
UCLASS()
class TEST_API UCombatAuthoringLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Python sample_data edits do not rebuild UE's cached triangulation. */
    UFUNCTION(BlueprintCallable, Category="Combat|Authoring", meta=(DevelopmentOnly))
    static bool RebuildBlendSpace(UBlendSpace* BlendSpace);
    /** 에디터 회귀 검사에서 실제 애니메이션 상태를 확인한다. 포즈는 수정하지 않는다. */
    UFUNCTION(BlueprintPure, Category="Combat|Verification", meta=(DevelopmentOnly))
    static FName GetAnimationState(USkeletalMeshComponent* Mesh, FName Machine);
    /** 에디터 검증 전용: 실제 스키닝된 신발 밑면의 최저점을 좌/우 순으로 반환한다.
     * 렌더 스레드를 동기화하므로 게임 Tick에서 호출하면 안 된다. */
    UFUNCTION(BlueprintCallable, Category="Combat|Verification", meta=(DevelopmentOnly))
    static TArray<FVector> MeasureShoeSoles(USkeletalMeshComponent* Mesh, int32 MaterialIndex = -1, int32 Region = 0);
};
