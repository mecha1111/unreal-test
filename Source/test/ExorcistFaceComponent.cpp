#include "ExorcistFaceComponent.h"
#include "Playground.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "KawaiiPhysicsLibrary.h"

UExorcistFaceComponent::UExorcistFaceComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 1.f / 30.f;
}

void UExorcistFaceComponent::BeginPlay()
{
    Super::BeginPlay();
    Player = Cast<APlaygroundCharacter>(GetOwner());
    if (Player)
    {
        AddTickPrerequisiteActor(Player);
        // Apply garment settings before this frame's parallel mesh evaluation starts.
        Player->GetMesh()->AddTickPrerequisiteComponent(this);
        LastHealth = Player->Health;
    }
}

FVector UExorcistFaceComponent::AttachmentLocation(USkeletalMeshComponent* Mesh, FName LegacyName)
{
    if (!Mesh) return FVector::ZeroVector;
    FName Bone = LegacyName;
    if (LegacyName == TEXT("hand_l")) Bone = TEXT("hand_L");
    if (LegacyName == TEXT("hand_r")) Bone = TEXT("hand_R");
    if (LegacyName == TEXT("foot_l")) Bone = TEXT("foot_L");
    if (LegacyName == TEXT("foot_r")) Bone = TEXT("foot_R");
    if (LegacyName == TEXT("lowerarm_l")) Bone = TEXT("lower_arm_L");
    if (LegacyName == TEXT("lowerarm_r")) Bone = TEXT("lower_arm_R");
    if (Mesh->GetBoneIndex(Bone) == INDEX_NONE) Bone = LegacyName;
    const FVector Location = Mesh->GetSocketLocation(Bone);
    if (LegacyName == TEXT("hand_l") || LegacyName == TEXT("hand_r"))
    {
        const FName Finger = LegacyName == TEXT("hand_l") ? TEXT("middle_proximal_L") : TEXT("middle_proximal_R");
        if (Mesh->GetBoneIndex(Finger) != INDEX_NONE)
            return FMath::Lerp(Location, Mesh->GetSocketLocation(Finger), .75f);
    }
    return Location;
}

FVector UExorcistFaceComponent::StrikeLocation(USkeletalMeshComponent* Mesh, int32 Variant)
{
    if (!Mesh) return FVector::ZeroVector;
    if (Variant == 3 || Variant == 6)
    {
        const FVector Foot = AttachmentLocation(Mesh, TEXT("foot_r"));
        return Mesh->GetBoneIndex(TEXT("toes_R")) != INDEX_NONE
            ? FMath::Lerp(Foot, Mesh->GetSocketLocation(TEXT("toes_R")), .8f) : Foot;
    }
    return AttachmentLocation(Mesh, Variant == 0 || Variant == 4 ? TEXT("hand_l") : TEXT("hand_r"));
}

FVector UExorcistFaceComponent::StrikeBaseLocation(USkeletalMeshComponent* Mesh, int32 Variant)
{
    if (!Mesh) return FVector::ZeroVector;
    if (Variant == 3 || Variant == 6) return Mesh->GetSocketLocation(TEXT("lower_leg_R"));
    return AttachmentLocation(Mesh, Variant == 0 || Variant == 4 ? TEXT("lowerarm_l") : TEXT("lowerarm_r"));
}

void UExorcistFaceComponent::TickComponent(float DeltaTime, ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!Player || !Player->GetMesh()) return;
    USkeletalMeshComponent* Mesh = Player->GetMesh();
    // 히트스톱 중 얼굴도 공격 포즈와 함께 멈춘다.
    if (Mesh->GlobalAnimRateScale <= 0.f) return;
    FaceClock += DeltaTime;
    if (Player->Health < LastHealth) HurtUntil = FaceClock + .45f;
    LastHealth = Player->Health;
    const bool bHurt = FaceClock < HurtUntil;
    const bool bAttack = Player->bAttacking;
    const bool bUltimate = bAttack && Player->GetAttackVariant() == 5;
    const bool bEffort = bAttack && Player->AttackPhase == 2;
    const bool bIdle = !bAttack && !bHurt && !Player->GetCharacterMovement()->IsFalling() && Player->GetVelocity().SizeSquared2D()<100.f;
    // Resting garment collisions can fight the skinned pose indefinitely. Blend the
    // garment solver out at rest; retain authored idle motion and independent hair.
    const bool bRestingCloth = bIdle && Player->GetCharacterMovement()->GetCurrentAcceleration().SizeSquared2D()<1.f;
    ClothPhysicsWeight = FMath::FInterpConstantTo(ClothPhysicsWeight, bRestingCloth ? 0.f : 1.f,
        DeltaTime, bRestingCloth ? 3.5f : 8.f);
    UAnimInstance* PostProcess = Mesh->GetPostProcessInstance();
    if (PostProcess && (ClothAnimInstance.Get() != PostProcess || AppliedClothWeight != ClothPhysicsWeight))
    {
        TArray<FKawaiiPhysicsReference> Nodes;
        UKawaiiPhysicsLibrary::CollectKawaiiPhysicsNodesFromComponent(Nodes, Mesh, FGameplayTagContainer(), false);
        for (const FKawaiiPhysicsReference& Node : Nodes)
        {
            const FString Root = UKawaiiPhysicsLibrary::GetRootBoneName(Node).ToString();
            if (Root.StartsWith(TEXT("skirt_")) || Root.StartsWith(TEXT("Spring_")))
            {
                Node.CallAnimNodeFunction<FAnimNode_KawaiiPhysics>(TEXT("SetRestingGarmentWeight"),
                    [this](FAnimNode_KawaiiPhysics& Physics) { Physics.Alpha = ClothPhysicsWeight; });
            }
        }
        if (!Nodes.IsEmpty()) { ClothAnimInstance = PostProcess; AppliedClothWeight = ClothPhysicsWeight; }
    }
    IdleTime = bIdle ? IdleTime + DeltaTime : 0.f;
    const float Cycle=FMath::Fmod(FMath::Max(0.f,IdleTime-6.f),15.f);
    IdleExpression=IdleTime<6.f?0:1+static_cast<int32>(Cycle/5.f);
    const float Local=FMath::Fmod(Cycle,5.f);
    const float Ease=FMath::SmoothStep(0.f,.9f,Local)*(1.f-FMath::SmoothStep(3.2f,4.8f,Local));
    IdleExpressionWeight=FMath::FInterpTo(IdleExpressionWeight,bIdle&&IdleExpression>0?Ease:0.f,DeltaTime,7.f);
    const float IdleWeight=bAttack||bHurt?0.f:IdleExpressionWeight;
    const float PhaseWeight=Player->AttackPhase==0?.4f:Player->AttackPhase==3?.22f:1.f;
    const float Desired = bHurt ? .8f : bAttack ? (bUltimate ? .85f : .55f)*PhaseWeight : 0.f;
    ExpressionIntensity = FMath::FInterpTo(ExpressionIntensity, Desired, DeltaTime, 16.f);
    const float DesiredMouth = bHurt ? .25f : bEffort ? (bUltimate ? .60f : .20f)
        : Player->bRunning ? .08f : 0.f;
    MouthOpen = FMath::FInterpTo(MouthOpen, DesiredMouth, DeltaTime, 18.f);
    if(FaceClock>=NextBlink && !bAttack){BlinkStart=FaceClock;NextBlink=FaceClock+2.6f+FMath::Fmod(++BlinkIndex*1.37f,2.3f);}
    const float BlinkPhase=FaceClock-BlinkStart;
    Blink = !bAttack && BlinkPhase < .17f ? FMath::Sin(BlinkPhase / .17f * PI) : 0.f;
    Mesh->SetMorphTarget(TEXT("EA_blink"), Blink);
    Mesh->SetMorphTarget(TEXT("EA_angry_eye"), bHurt ? 0.f : ExpressionIntensity * .7f);
    Mesh->SetMorphTarget(TEXT("EA_angry_brow"), bHurt ? 0.f : ExpressionIntensity);
    Mesh->SetMorphTarget(TEXT("EA_sad_eye"), bHurt ? ExpressionIntensity * .5f : 0.f);
    Mesh->SetMorphTarget(TEXT("EA_angry_mouth"), bAttack ? ExpressionIntensity * .25f : 0.f);
    Mesh->SetMorphTarget(TEXT("EA_aa"), MouthOpen);
    auto Blend=[&](FName Name,float Target){Mesh->SetMorphTarget(Name,FMath::FInterpTo(Mesh->GetMorphTarget(Name),Target,DeltaTime,10.f));};
    Blend(TEXT("EA_relaxed_eye"),bAttack||bHurt?0.f:.08f+(IdleExpression==1?.28f*IdleWeight:0.f));
    Blend(TEXT("EA_relaxed_brow"),IdleExpression==1?.3f*IdleWeight:0.f);
    Blend(TEXT("EA_relaxed_mouth"),IdleExpression==1?.18f*IdleWeight:0.f);
    Blend(TEXT("EA_happy_eye"),IdleExpression==3?.18f*IdleWeight:0.f);
    Blend(TEXT("EA_happy_brow"),IdleExpression==3?.23f*IdleWeight:0.f);
    Blend(TEXT("EA_happy_mouth"),IdleExpression==3?.32f*IdleWeight:0.f);
    Blend(TEXT("EA_surprised_brow"),IdleExpression==2?.16f*IdleWeight:0.f);
    Blend(TEXT("EA_lookLeft"),IdleExpression==2?.30f*IdleWeight:0.f);
    Blend(TEXT("EA_lookRight"),IdleExpression==3?.12f*IdleWeight:0.f);
    Blend(TEXT("EA_lookDown"),IdleExpression==1?.10f*IdleWeight:0.f);
}
