#pragma once

#include "CoreMinimal.h"
#include "Components/SkeletalMeshComponent.h"
#include "ComicSteppedMeshComponent.generated.h"

/** 표시할 뼈 포즈만 일정 간격으로 유지한다. 애니메이션 시간·노티파이·캐릭터 이동은 매 틱 진행한다. */
UCLASS()
class TEST_API UComicSteppedMeshComponent : public USkeletalMeshComponent
{
	GENERATED_BODY()
public:
	virtual void TickPose(float DeltaTime, bool bNeedsValidRootMotion) override;
	virtual void FinalizeBoneTransform() override;
	/** 초당 표시 포즈 수. 0이면 제한 해제. 접촉 구간은 높은 값으로 바꾸어 포즈 지연을 막는다. */
	void SetPoseCadence(float FramesPerSecond);
	/** 다음 평가 결과를 반드시 표시한다. 공격 시작, 순간 이동, 새 피격 클립에서 호출한다. */
	void ResetPoseCadence();

private:
	TArray<FTransform> HeldComponentPose;
	float PoseInterval = 1.f / 18.f;
	float PoseElapsed = 1.f;
	bool bForceSample = true;
};
