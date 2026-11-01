#include "CombatAuthoringLibrary.h"
#include "Animation/BlendSpace.h"
#include "Animation/AnimInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "SkeletalRenderPublic.h"
#include "Engine/SkeletalMesh.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkeletalMeshLODRenderData.h"

TArray<FVector> UCombatAuthoringLibrary::MeasureShoeSoles(USkeletalMeshComponent* Mesh, int32 MaterialIndex, int32 Region)
{
    TArray<FVector> Result;
#if WITH_EDITOR
    if (!Mesh || !Mesh->GetSkeletalMeshAsset()) return Result;
    TArray<FFinalSkinVertex> Vertices;
    Mesh->GetCPUSkinnedVertices(Vertices, 0);
    const FVector Left = Mesh->GetSocketLocation(TEXT("foot_L"));
    const FVector Right = Mesh->GetSocketLocation(TEXT("foot_R"));
    const FVector Directions[2] = {(Mesh->GetSocketLocation(TEXT("toes_L"))-Left).GetSafeNormal2D(),
        (Mesh->GetSocketLocation(TEXT("toes_R"))-Right).GetSafeNormal2D()};
    TArray<bool> Allowed;
    Allowed.Init(MaterialIndex < 0, Vertices.Num());
    if (MaterialIndex >= 0)
        for (const FSkelMeshRenderSection& Section : Mesh->GetSkeletalMeshAsset()->GetResourceForRendering()->LODRenderData[0].RenderSections)
            if (Section.MaterialIndex == MaterialIndex)
                for (uint32 I=Section.BaseVertexIndex; I<Section.BaseVertexIndex+Section.NumVertices && I<uint32(Allowed.Num()); ++I) Allowed[I]=true;
    FVector Soles[2] = {FVector(0,0,DBL_MAX), FVector(0,0,DBL_MAX)};
    for (int32 VertexIndex=0; VertexIndex<Vertices.Num(); ++VertexIndex)
    {
        if (!Allowed[VertexIndex]) continue;
        const FFinalSkinVertex& Vertex = Vertices[VertexIndex];
        const FVector World = Mesh->GetComponentTransform().TransformPosition(FVector(Vertex.Position));
        const float DL = FVector::DistSquaredXY(World, Left);
        const float DR = FVector::DistSquaredXY(World, Right);
        const int32 Side = DL < DR ? 0 : 1;
        const FVector& Foot = Side == 0 ? Left : Right;
        const float Along = FVector::DotProduct(World-Foot,Directions[Side]);
        if ((Region == 1 && Along > -1.f) || (Region == 2 && Along < 7.f)) continue;
        if (FMath::Min(DL, DR) < FMath::Square(25.f) && World.Z < Foot.Z && World.Z < Soles[Side].Z)
            Soles[Side] = World;
    }
    if (Soles[0].Z < DBL_MAX && Soles[1].Z < DBL_MAX)
    {
        Result.Add(Soles[0]); Result.Add(Soles[1]);
    }
#endif
    return Result;
}

FName UCombatAuthoringLibrary::GetAnimationState(USkeletalMeshComponent* Mesh, FName Machine)
{
    UAnimInstance* Anim = Mesh ? Mesh->GetAnimInstance() : nullptr;
    if (!Anim) return NAME_None;
    const int32 Index = Anim->GetStateMachineIndex(Machine);
    return Index != INDEX_NONE ? Anim->GetCurrentStateName(Index) : NAME_None;
}
bool UCombatAuthoringLibrary::RebuildBlendSpace(UBlendSpace* BlendSpace)
{
#if WITH_EDITOR
    if (!BlendSpace) return false;
    BlendSpace->ResampleData();
    BlendSpace->MarkPackageDirty();
    return true;
#else
    return false;
#endif
}
