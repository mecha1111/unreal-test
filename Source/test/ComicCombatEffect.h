#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ComicCombatEffect.generated.h"

class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UTexture2D;
class UNiagaraComponent;
class UNiagaraSystem;
class UProceduralMeshComponent;

UENUM()
enum class EComicEffect : uint8
{
	Trail, Impact, HeavyImpact, UltimateImpact, Charge, Speed, Question, JumpTakeoff, AirJump, Landing, Rush, Recovery
};

/** 각 그림 레이어의 수명과 공간을 독립적으로 관리한다. 게임 피해 판정은 하지 않는다. */
USTRUCT()
struct FComicEffectLayer
{
	GENERATED_BODY()
	UPROPERTY() TObjectPtr<UStaticMeshComponent> Mesh;
	UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> Material;
	FVector Offset = FVector::ZeroVector;
    FVector SurfaceExpansionDirection = FVector::ZeroVector;
    float ExpansionRate = 65.f;
	FVector Velocity = FVector::ZeroVector;
	FVector Acceleration = FVector::ZeroVector;
	FVector2D StartSize = FVector2D(20.f);
	FVector2D EndSize = FVector2D(100.f);
	float Delay = 0.f;
	float Duration = .25f;
	float Spin = 0.f;
	float Angle = 0.f;
	float Pop = .10f;
	float Wobble = 0.f;
	float Stretch = 0.f;
	float Drag = 0.f;
	bool bGlyph = false;
	FQuat BaseRotation = FQuat::Identity;
	bool bBillboard = true;
	bool bFastExpand = false;
	float DepthScale = 1.f;
	bool bVolume = false;
	FVector StartScale = FVector(.1f);
	FVector EndScale = FVector::OneVector;
	FRotator Tumble = FRotator::ZeroRotator;
};

/** 이미지가 아닌 실제 공간 선분. 재생 중 분기 경로가 바뀌고 빠르게 소멸한다. */
USTRUCT()
struct FComicElectricSegment
{
	GENERATED_BODY()
	UPROPERTY() TObjectPtr<UStaticMeshComponent> Mesh;
	UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> Material;
	FVector Start;
	FVector End;
	float Seed = 0.f;
	float Delay = 0.f;
	float Duration = .2f;
	float Width = .65f;
};

/** AE식 타격 레이어: 중심, 잉크 면, 링, 속도선, 파편을 월드 공간에서 합성한다. */
UCLASS()
class TEST_API AComicCombatEffect : public AActor
{
	GENERATED_BODY()
public:
	AComicCombatEffect();
	virtual void Tick(float DeltaSeconds) override;
	/** 비활성 인스턴스만 재생한다. 풀 보관 시 수명 종료 후 숨기고 Tick을 끈다. */
	void Initialize(EComicEffect Kind, const FVector& Direction, int32 Variant = 0, bool bRetain = false);
	/** 공격 취소 시 손을 따라다니던 준비/궤적만 정리하고 이미 발생한 접촉 파편은 남긴다. */
    void CancelAnticipation();
    bool CanReuseFor(EComicEffect Kind) const { return !bActive && CachedKind == Kind; }
	/** 풀에 남아 있는 객체와 실제 재생 중인 효과를 구분한다. */
	UFUNCTION(BlueprintPure, Category = "VFX") bool IsEffectActive() const { return bActive; }

private:
    bool bFollowHand = false;
    bool bFollowBody = false;
    UPROPERTY() TArray<TObjectPtr<UTexture2D>> AnimatedTextures;
    UPROPERTY() TObjectPtr<UMaterialInterface> AnimatedMaterial;
    UPROPERTY() TObjectPtr<UMaterialInterface> AnimatedLitMaterial;
    FComicEffectLayer& AddAnimated(int32 Part, float Delay, float Life, const FVector2D& Size, bool bBillboard = true);
	UPROPERTY() TObjectPtr<UStaticMesh> HifiShard;
	UPROPERTY() TObjectPtr<UStaticMesh> HifiCrown;
	UPROPERTY() TObjectPtr<UStaticMesh> HifiRing;
	UPROPERTY() TObjectPtr<UStaticMesh> HifiSweep;
	UPROPERTY() TObjectPtr<UStaticMesh> HifiSmoke;
	UPROPERTY() TObjectPtr<UMaterialInterface> HifiMeshMaterial;
	UPROPERTY() TObjectPtr<UMaterialInterface> HifiFlipbookMaterial;
	UPROPERTY() TObjectPtr<UNiagaraComponent> ImpactSparks;
	UPROPERTY() TObjectPtr<UNiagaraSystem> SparkSystem;
	UPROPERTY() TObjectPtr<UProceduralMeshComponent> TrackedRibbon;
	UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> TrackedRibbonMaterial;
	TArray<FVector> HandSamples;
	TArray<FVector> WristSamples;
    TArray<float> RibbonSampleTimes;
    TArray<FVector> RibbonVertices;
    TArray<FVector> RibbonNormals;
    TArray<FVector2D> RibbonUVs;
    TArray<int32> RibbonIndices;
	int32 AttackVariant = 0;
	FComicEffectLayer& AddVolume(UStaticMesh* Mesh, const FLinearColor& Tint,
		float Delay, float Life, const FVector& Scale, int32 Kind = 0);
	void AddHifiImpact(EComicEffect Kind, int32 Variant, const FVector& TowardCamera);
	void UpdateTrackedRibbon();
	UPROPERTY() TObjectPtr<UStaticMesh> Plane;
	UPROPERTY() TObjectPtr<UStaticMesh> ArcMesh;
	UPROPERTY() TObjectPtr<UStaticMesh> CylinderMesh;
	UPROPERTY() TObjectPtr<UStaticMesh> ConeMesh;
	UPROPERTY() TObjectPtr<UMaterialInterface> ShapeMaterial;
	UPROPERTY() TObjectPtr<UMaterialInterface> RibbonMaterial;
	UPROPERTY() TObjectPtr<UMaterialInterface> SpriteMaterial;
	UPROPERTY() TObjectPtr<UMaterialInterface> BurstMaterial;
	UPROPERTY() TObjectPtr<UMaterialInterface> PaintMaterial;
	UPROPERTY() TObjectPtr<UMaterialInterface> FlashMaterial;
	UPROPERTY() TObjectPtr<UMaterialInterface> SmearMaterial;
	UPROPERTY() TObjectPtr<UMaterialInterface> EnergyMaterial;
	UPROPERTY() TArray<TObjectPtr<UTexture2D>> ImpactTextures;
	UPROPERTY() TArray<TObjectPtr<UTexture2D>> PaintedTextures;
	UPROPERTY() TObjectPtr<UMaterialInterface> PaintedMaterial;
	UPROPERTY() TObjectPtr<UMaterialInterface> MovementMaterial;
	UPROPERTY() TArray<FComicEffectLayer> EffectLayers;
	UPROPERTY() TArray<FComicElectricSegment> ElectricSegments;
	float Age = 0.f;
	float Duration = 0.f;
	int32 ActiveLayerCount = 0;
	int32 ActiveElectricCount = 0;
	bool bActive = false;
	bool bRetained = false;
	EComicEffect CachedKind = EComicEffect::Question;
	void FinishEffect();
	FVector Forward = FVector::ForwardVector;
	void AddMovementLayers(EComicEffect Kind, int32 Variant, const FVector& Right);
	FComicEffectLayer& AddPainted(int32 Part, float Delay, float Lifetime, const FVector2D& Size,
		bool bBillboard = true, float HueOffset = 0.f, float Energy = 2.4f);
	void AddElectric(const FVector& Start, const FVector& End, const FLinearColor& Color, float Delay, float Lifetime, float Width, float Seed);
	FComicEffectLayer& AddLayer(int32 Shape, const FLinearColor& Tint, float Delay,
		float Lifetime, const FVector2D& StartSize, const FVector2D& EndSize,
		bool bBillboard = true, UTexture2D* Texture = nullptr, UMaterialInterface* OverrideMaterial = nullptr);
};
