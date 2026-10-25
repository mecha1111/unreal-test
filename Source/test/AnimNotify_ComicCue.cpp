#include "AnimNotify_ComicCue.h"
#include "Playground.h"
#include "Components/SkeletalMeshComponent.h"

void UAnimNotify_ComicCue::Notify(USkeletalMeshComponent* MeshComp,
	UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
	Super::Notify(MeshComp, Animation, EventReference);
	if (MeshComp)
	{
		if (APlaygroundCharacter* Character = Cast<APlaygroundCharacter>(MeshComp->GetOwner()))
		{
			Character->HandleCombatCue(Cue, Animation);
		}
	}
}

FString UAnimNotify_ComicCue::GetNotifyName_Implementation() const
{
	return Cue == 0 ? TEXT("Comic / Trail") : Cue == 1 ? TEXT("Comic / Strike") : TEXT("Comic / Recover");
}
