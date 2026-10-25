#include "ComicSteppedMeshComponent.h"
#include "Engine/World.h"

void UComicSteppedMeshComponent::SetPoseCadence(float FramesPerSecond)
{
	const float Interval = FramesPerSecond > 0.f ? 1.f / FramesPerSecond : 0.f;
	if (!FMath::IsNearlyEqual(Interval, PoseInterval)) bForceSample = true;
	PoseInterval = Interval;
}

void UComicSteppedMeshComponent::ResetPoseCadence()
{
	bForceSample = true;
	PoseElapsed = 0.f;
}

void UComicSteppedMeshComponent::TickPose(float DeltaTime, bool bNeedsValidRootMotion)
{
	PoseElapsed += DeltaTime;
	Super::TickPose(DeltaTime, bNeedsValidRootMotion);
}

void UComicSteppedMeshComponent::FinalizeBoneTransform()
{
	// 병렬 평가 완료 후 게임 스레드에서 쓰기 버퍼를 조정한다. 엔진의 버퍼 교환/노티파이는 그대로 호출한다.
	if (GetWorld() && GetWorld()->IsGameWorld() && !IsSimulatingPhysics())
	{
		TArray<FTransform>& Pose = GetEditableComponentSpaceTransforms();
		if (PoseInterval <= 0.f || bForceSample || HeldComponentPose.Num() != Pose.Num()
			|| PoseElapsed + UE_SMALL_NUMBER >= PoseInterval)
		{
			HeldComponentPose = Pose;
			PoseElapsed = PoseInterval > 0.f ? FMath::Fmod(PoseElapsed, PoseInterval) : 0.f;
			bForceSample = false;
		}
		else
		{
			Pose = HeldComponentPose;
		}
	}
	Super::FinalizeBoneTransform();
}
