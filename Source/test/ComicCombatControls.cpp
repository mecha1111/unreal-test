#include "Playground.h"
#include "ComicCombatPresentationComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"

// 한 입력만 보관한다. 같은 버튼 연타는 짧은 후속 동작을 기다릴 만큼만 더 보관한다.
void APlaygroundCharacter::RequestAction(int32 Action)
{
    if (Action == 5 && UltimateCharge < 99.99f) return;
    if (Action == 4 && GetWorld()->GetTimeSeconds() < DashReadyAt) return;
    BufferedAction = Action;
    const bool bRepeatLight = bAttacking && ActiveAttack < 3 && Action == 0;
    const bool bRepeatHeavy = bAttacking && ActiveAttack == 3 && Action == 1;
    BufferedUntil = GetWorld()->GetRealTimeSeconds() + (bRepeatHeavy ? .40f : bRepeatLight ? .32f : .24f);
    ConsumeBufferedAction();
}

void APlaygroundCharacter::ConsumeBufferedAction()
{
    if (BufferedAction < 0) return;
    if (GetWorld()->GetRealTimeSeconds() > BufferedUntil)
    {
        BufferedAction = -1;
        return;
    }
    if (PoseHoldUntil > GetWorld()->GetTimeSeconds()) return;
    // 명중 이후나 회복 구간에서 다음 공격으로 취소할 수 있다. Ctrl/점프는 별도로 즉시 취소한다.
    if (bAttacking && !bStrikeResolved && AttackPhase != 3) return;
    // 같은 버튼을 난타해도 접촉 포즈에서 즉시 첫 포즈로 되감지 않는다.
    // 다른 버튼의 의도적인 캔슬은 기존처럼 즉시 허용한다.
    const bool bRepeatedButton = (ActiveAttack < 3 && BufferedAction == 0)
        || (ActiveAttack == 3 && BufferedAction == 1);
    const float RepeatEntryTimes[] = {.20f,.25f,.38f,.49f};
    if (bAttacking && bRepeatedButton && AttackClipTime < RepeatEntryTimes[ActiveAttack]) return;
    const int32 Action = BufferedAction;
    BufferedAction = -1;
    if (Action == 5 && UltimateCharge < 99.99f) return;
    if (Action == 4 && GetWorld()->GetTimeSeconds() < DashReadyAt) return;
    if (!bAttacking && GetWorld()->GetTimeSeconds()-LastComboEndTime > .75f) LightChain = 0;
    int32 Variant = Action;
    if (Action == 0) Variant = LightChain;
    if (Action == 1) Variant = LightChain == 2 ? 7 : 3;
    if (GetCharacterMovement()->IsFalling())
    {
        if (Action == 4 || Action == 5) return;
        Variant = 6;
    }
    bStartingLight = Action == 0 && Variant != 6;
    StartAttack(Variant);
    bStartingLight = false;
}

void APlaygroundCharacter::CancelAttack()
{
    BufferedAction = -1;
    BufferedUntil = -1.f;
    LightChain = 0;
    if (!bAttacking) return;
    ++CancelCount;
    UAnimMontage* Previous = ActiveMontage;
    ActiveMontage = nullptr; // 종료 델리게이트가 새 상태를 다시 종료하지 않도록 먼저 분리한다.
    if (UAnimInstance* Anim = GetMesh()->GetAnimInstance()) Anim->Montage_Stop(0.f,Previous);
    FinishAttack();
    CombatPresentation->CancelPresentation();
    GetCharacterMovement()->StopMovementImmediately();
}

bool APlaygroundCharacter::HasClearCombatPath(const APlaygroundTarget* Target) const
{
    if (!IsValid(Target)) return false;
    FHitResult Hit;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(CombatAssistVisibility),false,this);
    return !GetWorld()->LineTraceSingleByChannel(Hit,GetActorLocation()+FVector(0,0,25),
        Target->GetActorLocation()+FVector(0,0,25),ECC_Visibility,Query) || Hit.GetActor() == Target;
}

APlaygroundTarget* APlaygroundCharacter::FindAssistedTarget(const FVector& Direction,float Range,float MinDot) const
{
    APlaygroundTarget* Best = nullptr;
    float BestScore = TNumericLimits<float>::Max();
    for (TActorIterator<APlaygroundTarget> It(GetWorld()); It; ++It)
    {
        const FVector Delta = It->GetActorLocation()-GetActorLocation();
        const float Distance = Delta.Size2D();
        const float Alignment = FVector::DotProduct(Delta.GetSafeNormal2D(),Direction);
        if (Distance > Range || FMath::Abs(Delta.Z) > 180.f || Alignment < MinDot || !HasClearCombatPath(*It)) continue;
        const float Score = Distance + (1.f-Alignment)*Range*.65f;
        if (Score < BestScore) { Best = *It; BestScore = Score; }
    }
    return Best;
}
