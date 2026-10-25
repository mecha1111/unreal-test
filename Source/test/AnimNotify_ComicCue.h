#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "AnimNotify_ComicCue.generated.h"

/** 공격 클립의 실제 키 시점에서 궤적, 명중 판정, 연계 허용을 전달한다. */
UCLASS()
class TEST_API UAnimNotify_ComicCue : public UAnimNotify
{
	GENERATED_BODY()
public:
	/** 0: 궤적 시작, 1: 명중 판정, 2: 다음 공격 연계 허용. */
	UPROPERTY(EditAnywhere, Category="Combat", meta=(ClampMin="0", ClampMax="2"))
	int32 Cue = 1;

	virtual void Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation,
		const FAnimNotifyEventReference& EventReference) override;
	virtual FString GetNotifyName_Implementation() const override;
};
