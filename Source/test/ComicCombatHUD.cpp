#include "Playground.h"
#include "CanvasItem.h"
#include "Engine/Canvas.h"
#include "Engine/FontFace.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Fonts/CompositeFont.h"
#include "Fonts/FontMeasure.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "InputKeyEventArgs.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/PlayerCameraManager.h"
#if WITH_EDITOR
#include "Framework/Commands/InputBindingManager.h"
#include "Framework/Commands/UICommandInfo.h"
#endif

namespace CombatUI
{
    FLinearColor Hex(uint32 RGB, float Alpha=1.f)
    {
        FLinearColor C(FColor((RGB>>16)&255,(RGB>>8)&255,RGB&255)); C.A=Alpha; return C;
    }
    const FLinearColor Ink=Hex(0x090810), Ivory=Hex(0xfaf5df), Cyan=Hex(0x08ddd1), Yellow=Hex(0xffe21b);
    const FLinearColor Palette[]={Cyan,Yellow,Hex(0xff8b36),Hex(0xff387f)};

    // Vertices and UVs share one boundary, so the portrait is clipped by its angled frame.
    void Polygon(UCanvas* Canvas,const TArray<FVector2D>& Points,FLinearColor Color,UTexture* Texture=nullptr,
        const TArray<FVector2D>& UVs={})
    {
        if(Points.Num()<3) return;
        TArray<FCanvasUVTri> Tris;
        for(int32 I=1;I<Points.Num()-1;++I)
        {
            FCanvasUVTri T;
            T.V0_Pos=Points[0];T.V1_Pos=Points[I];T.V2_Pos=Points[I+1];
            T.V0_UV=UVs.IsEmpty()?FVector2D::ZeroVector:UVs[0];
            T.V1_UV=UVs.IsEmpty()?FVector2D::ZeroVector:UVs[I];
            T.V2_UV=UVs.IsEmpty()?FVector2D::ZeroVector:UVs[I+1];
            T.V0_Color=T.V1_Color=T.V2_Color=Color;Tris.Add(T);
        }
        Canvas->K2_DrawTriangle(Texture,Tris);
    }
    UFont* Font(UObject* Outer,UFontFace* Face,UFontFace* Korean=nullptr)
    {
        UFont* Result=NewObject<UFont>(Outer);
        Result->FontCacheType=EFontCacheType::Runtime;
        FTypefaceEntry Entry(NAME_None);Entry.Font=FFontData(Face);
        Result->GetMutableInternalCompositeFont().DefaultTypeface.Fonts.Add(Entry);
        if(Korean){FTypefaceEntry Fallback(NAME_None);Fallback.Font=FFontData(Korean);Result->GetMutableInternalCompositeFont().FallbackTypeface.Typeface.Fonts.Add(Fallback);}
        return Result;
    }
}

float APlaygroundCharacter::GetFlurryCooldown() const
{
    return FMath::Max(0.f,DashReadyAt-GetWorld()->GetTimeSeconds());
}

float APlaygroundCharacter::TakeDamage(float Damage,const FDamageEvent& Event,AController* EventInstigator,AActor* Causer)
{
    const float Applied=FMath::Clamp(Super::TakeDamage(Damage,Event,EventInstigator,Causer),0.f,Health);
    Health-=Applied;return Applied;
}

void APlaygroundHUD::DrawCombatInterface(APlaygroundCharacter* Player)
{
    using namespace CombatUI;
    if(!HudDisplayFont || !HudBodyFont)
    {
        HudDisplayFont=Font(this,HudDisplayFace,HudBodyBoldFace);
        HudBodyFont=Font(this,HudLatinFace,HudBodyFace);
        HudBoldFont=Font(this,HudLatinBoldFace,HudBodyBoldFace);
        HudItalicFont=Font(this,HudLatinItalicFace,HudBodyBoldFace);
    }
    const float Now=GetWorld()->GetTimeSeconds();
    const float Dt=HudPreviousFrame<0.f?0.f:FMath::Clamp(Now-HudPreviousFrame,0.f,.1f);
    HudPreviousFrame=Now;
    if(HudPreviousHealth>Player->Health) HudLastDamage=Now;
    HudPreviousHealth=Player->Health;
    DisplayHealth=FMath::FInterpTo(DisplayHealth,Player->Health,Dt,13.f);
    if(FMath::Abs(DisplayHealth-Player->Health)<.1f)DisplayHealth=Player->Health;
    DisplayUltimate=FMath::FInterpTo(DisplayUltimate,Player->UltimateCharge,Dt,13.f);
    if(FMath::Abs(DisplayUltimate-Player->UltimateCharge)<.1f)DisplayUltimate=Player->UltimateCharge;
    if(Player->HitCount!=HudObservedHits)
    {
        if(Now-HudLastHit>2.5f){HudComboCount=0;HudComboStarted=Now;}
        HudComboCount+=FMath::Max(0,Player->HitCount-HudObservedHits);
        HudObservedHits=Player->HitCount;HudLastHit=Now;
    }
    HudComboRemaining=FMath::Max(0.f,2.5f-(Now-HudLastHit));
    if(Player->AttackCount!=HudObservedAttacks){HudLastAttack=Now;HudObservedAttacks=Player->AttackCount;}
    HudUnit=FMath::Clamp(Canvas->SizeY/1080.f,1.f,1.5f);
    const float U=HudUnit,W=Canvas->SizeX/U,H=Canvas->SizeY/U;
    const bool Small=W<=650.f,Medium=W<=1050.f;
    const float Safe=Small?20.f:FMath::Clamp(W*.035f,22.f,58.f);
    InterfaceRegions.Reset();
    auto Rect=[&](float X,float Y,float BW,float BH,FLinearColor Color){DrawRect(Color,X*U,Y*U,BW*U,BH*U);};
    auto Poly=[&](const TArray<FVector2D>& P,FLinearColor C){TArray<FVector2D> A;for(auto V:P)A.Add(V*U);Polygon(Canvas,A,C);};
    auto Region=[&](FName Name,float X,float Y,float BW,float BH){InterfaceRegions.Add(Name,FBox2D(FVector2D(X,Y)*U,FVector2D(X+BW,Y+BH)*U));};
    auto Text=[&](const FString& Value,float X,float Y,float Size,FLinearColor Color,bool Display=false,float Align=0.f,int32 Style=0,float Tracking=0.f)
    {
        UFont* Selected=Style==1?HudItalicFont.Get():Style==2?HudBoldFont.Get():Display?HudDisplayFont.Get():HudBodyFont.Get();
        FSlateFontInfo Info(Selected,Size*.75f*U);
        Info.LetterSpacing=FMath::RoundToInt(Tracking/Size*1000.f);
        const bool Korean=Value.Contains(TEXT("연타"))||Value.Contains(TEXT("궁극기"));
        const bool Slant=(Display&&Style==0)||(Style==1&&Korean);
        float TX=X*U;
        if(Align!=0.f)TX-=FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Value,Info).X*Align;
        FMatrix Transform=FMatrix::Identity;
        if(Slant)Transform.M[1][0]=(Value==TEXT("E")||Value==TEXT("Q"))?-.27f:-.2126f;
        Transform.M[3][0]=TX+(Slant?Size*.15f*U:0.f);Transform.M[3][1]=Y*U;
        Canvas->Canvas->PushRelativeTransform(Transform);
        FCanvasTextItem Item(FVector2D::ZeroVector,FText::FromString(Value),Info,Color);
        Item.EnableShadow(Ink.CopyWithNewOpacity(Color.A*.8f),FVector2D(U,U));
        Canvas->DrawItem(Item);
        Canvas->Canvas->PopTransform();
    };
    auto Meter=[&](float X,float Y,float BW,float BH,float Fill,FLinearColor C)
    {
        const float Slant=BH*.344f;
        Poly({{X+Slant,Y},{X+BW+Slant,Y},{X+BW,Y+BH},{X,Y+BH}},Hex(0x706080));
        Poly({{X+Slant+2,Y+2},{X+BW+Slant-2,Y+2},{X+BW-2,Y+BH-2},{X+2,Y+BH-2}},Ink);
        const float Inner=FMath::Max(0.f,BW-10),F=FMath::Clamp(Fill,0.f,1.f);
        Poly({{X+Slant+5,Y+5},{X+Slant+5+Inner,Y+5},{X+5+Inner,Y+BH-5},{X+5,Y+BH-5}},Hex(0x382944));
        if(F>0.f)Poly({{X+Slant+5,Y+5},{X+Slant+5+Inner*F,Y+5},{X+5+Inner*F,Y+BH-5},{X+5,Y+BH-5}},C);
    };

    // Left upper portrait / health / free-use ultimate.
    const float DamageAge=Now-HudLastDamage;
    const float Shake=DamageAge<.3f?FMath::Sin(DamageAge*80.f)*4.f*(1.f-DamageAge/.3f):0.f;
    const float X=Safe+Shake,Y=Small?23.f:W>=1700.f?38.f:30.f;
    const float PW=Small?52.f:Medium?65.f:90.f,PH=Small?65.f:Medium?80.f:100.f;
    const float Width=Small?270.f:Medium?330.f:FMath::Clamp(W*.36f,280.f,570.f);
    Poly({{X+PW*.23f,Y},{X+PW,Y},{X+PW*.77f,Y+PH},{X,Y+PH}},Ink);
    const float IX=X+5,IY=Y+5,IW=PW-10,IH=PH-10;
    const TArray<FVector2D> PortraitPoints={{IX+IW*.23f,IY},{IX+IW,IY},{IX+IW*.77f,IY+IH},{IX,IY+IH}};
    Poly(PortraitPoints,Cyan);
    if(Portrait)
    {
        TArray<FVector2D> Screen;for(auto P:PortraitPoints)Screen.Add(P*U);
        Polygon(Canvas,Screen,FLinearColor::White,Portrait,{{.21,.04},{.91,.04},{.91,.91},{.21,.91}});
    }
    const float VX=X+PW+(Medium?11.f:15.f),VW=Width-PW-(Medium?11.f:15.f),HPH=Medium?26.f:31.f;
    Text(TEXT("PLAYER"),VX,Y+2,Medium?18:22,Ivory,true,0,0,.6f);
    Meter(VX,Y+30,VW,HPH,DisplayHealth/FMath::Max(1.f,Player->MaxHealth),Player->Health<=250.f?Palette[3]:Cyan);
    Text(FString::Printf(TEXT("%d / %d"),FMath::RoundToInt(Player->Health),FMath::RoundToInt(Player->MaxHealth)),VX+VW-8,Y+34,Medium?14:17,Ivory,false,1,1);
    const float UY=Y+30+HPH+(Medium?9.f:12.f);
    Meter(VX,UY,VW-(Medium?82.f:108.f),Medium?12.f:15.f,DisplayUltimate/100.f,Yellow);
    Text(FString::Printf(TEXT("ULT %d%%"),FMath::FloorToInt(Player->UltimateCharge)),VX+VW,UY-3,Medium?13:17,Yellow,false,1,1);

    // Top center and a three-line menu affordance.
    const float TY=Small?119.f:W<=900.f?135.f:30.f;
    Text(TEXT("TRAINING"),W*.5f,TY,Small?11:15,Hex(0xb5aabd),false,.5f,2,1.f);
    Rect(W*.5f-89,TY+9,30,1,Hex(0x70627c));Rect(W*.5f+59,TY+9,30,1,Hex(0x70627c));
    Text(TEXT("전투 훈련"),W*.5f,TY+25,Small?9:12,Hex(0xb5aabd),false,.5f,0,2.f);
    const float MX=W-Safe-42,MY=Small?24.f:33.f;
    for(int32 I=0;I<3;++I)Rect(MX+7,MY+7+I*8,Small?23:28,2,Ivory);
    Region(TEXT("Menu"),MX,MY,42,38);

    // An actual-contact counter: 2.5 seconds of game time, paused and slowed with combat.
    const float Age=Now-HudLastHit;
    if(HudComboCount>0 && Age<2.78f)
    {
        const float EntranceAge=Now-HudComboStarted;
        const float Entrance=FMath::Clamp(EntranceAge/.10f,0.f,1.f);
        const float Alpha=FMath::Clamp((2.78f-Age)/.28f,0.f,1.f)*Entrance;
        const float Pop=(1.f+.12f*FMath::Exp(-Age*18.f))*(.88f+.12f*Entrance);
        const float CS=(Small?.62f:Medium?.8f:1.f)*Pop;
        const float CX=W-Safe-250*CS+(1.f-Alpha)*16,CY=H*(Small?.22f:Medium?.19f:.21f);
        Canvas->Canvas->PushRelativeTransform(FTranslationMatrix(FVector(-CX*U,-CY*U,0))*FRotationMatrix(FRotator(0,-8,0))*FTranslationMatrix(FVector(CX*U,CY*U,0)));
        auto P=[&](float PX,float PY){return FVector2D(CX+PX*CS,CY+PY*CS);};
        FLinearColor C=Palette[(HudComboCount-1)%4];C.A=Alpha;
        if(!ComboBackdropMaterial&&ComboBackdropBase)ComboBackdropMaterial=UMaterialInstanceDynamic::Create(ComboBackdropBase,this);
        if(ComboBackdropMaterial)
        {
            const int32 Index=(HudComboCount-1)%4;
            if(HudTintIndex!=Index){ComboBackdropMaterial->SetVectorParameterValue(TEXT("ComboTint"),Palette[Index]);HudTintIndex=Index;}
            ComboBackdropMaterial->SetScalarParameterValue(TEXT("Fade"),Alpha);
            Canvas->K2_DrawMaterial(ComboBackdropMaterial,P(-25,-10)*U,FVector2D(290,194)*CS*U,FVector2D::ZeroVector);
        }
        const FString Digits=FString::FromInt(HudComboCount);
        const float NumberSize=(Digits.Len()>2?80.f:104.f)*CS;
        FSlateFontInfo NumberInfo(HudDisplayFont.Get(),NumberSize*.75f*U);
        const float NumberWidth=FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Digits,NumberInfo).X/U;
        Text(Digits,CX+9*CS,CY+3*CS,NumberSize,C,true,0,0,-3.f*CS);
        Text(TEXT("HITS"),CX+17*CS+NumberWidth,CY+63*CS,39*CS,C,true,0,0,-1.f*CS);
        Text(TEXT("COMBO"),CX+232*CS,CY+109*CS,34*CS,Ivory.CopyWithNewOpacity(Alpha),true,1);
        Rect(CX+25*CS,CY+164*CS,215*CS,2,Hex(0xffffff,.07f*Alpha));
        Rect(CX+25*CS,CY+164*CS,215*CS*HudComboRemaining/2.5f,2,C);
        Canvas->Canvas->PopTransform();
    }

    // Four quiet rows; actions retain the existing game input and timing.
    const float Row=Small?30.f:Medium?33.f:38.f,KeySize=Small?13.f:Medium?16.f:18.f;
    const float NameSize=Small?11.f:Medium?13.f:15.f,KeyWidth=Small?55.f:80.f;
    const float Bottom=Small?22.f:Safe,Base=H-Bottom-(3*Row+21);
    const TCHAR* Keys[]={TEXT("LMB"),TEXT("RMB"),TEXT("SHIFT"),TEXT("SPACE")};
    const TCHAR* Names[]={TEXT("일반 공격"),TEXT("강공격"),TEXT("달리기"),TEXT("점프")};
    const bool Active[]={Player->bAttacking&&Player->GetAttackVariant()<3,Player->bAttacking&&Player->GetAttackVariant()==3,Player->bRunning,Player->GetCharacterMovement()->IsFalling()};
    for(int32 I=0;I<4;++I){const float HX=Safe+(Active[I]?4.f:0.f);Text(Keys[I],HX,Base+Row*I,KeySize,Active[I]?Cyan:Ivory,true);Text(Names[I],HX+KeyWidth,Base+Row*I+2,NameSize,Active[I]?Cyan:Ivory);}

    const float EWidth=Small?90.f:Medium?110.f:132.f,QWidth=Small?120.f:Medium?165.f:230.f,Gap=Small?12.f:Medium?19.f:28.f;
    const float AB=H-(W<=420.f?170.f:Bottom),AX=W-Safe-(EWidth+QWidth+2*Gap+1);
    const float KH=Small?48.f:Medium?65.f:82.f,NSize=Small?14.f:Medium?19.f:23.f,SSize=Small?12.f:Medium?17.f:21.f;
    const float Cooldown=Player->GetFlurryCooldown();
    for(int32 I=0;I<2;++I)
    {
        const float SX=I==0?AX:AX+EWidth+2*Gap+1,BW=I==0?EWidth:QWidth;
        const bool ActiveSkill=Player->bAttacking&&Player->GetAttackVariant()==(I==0?4:5);
        const float Bounce=ActiveSkill?FMath::Sin(FMath::Min(1.f,(Now-HudLastAttack)/.22f)*PI)*-6.f:0.f;
        const FLinearColor C=I==1?(Player->UltimateCharge>=99.99f||ActiveSkill?Yellow:Hex(0xa59b72)):Cooldown>0?Hex(0xa59bad):Cyan;
        Text(I==0?TEXT("E"):TEXT("Q"),SX,AB-KH-15+Bounce,KH,C,true);
        const float CopyX=SX+KH*.67f+10;
        Text(I==0?TEXT("연타"):TEXT("궁극기"),CopyX,AB-KH-9,NSize,C,false,0,1);
        FString Status=ActiveSkill?TEXT("ACTIVE"):I==0&&Cooldown>.001f?FString::Printf(TEXT("%.1f"),Cooldown):I==1&&Player->UltimateCharge<99.99f?FString::Printf(TEXT("%d%%"),FMath::FloorToInt(Player->UltimateCharge)):TEXT("READY");
        Text(Status,CopyX,AB-KH+NSize+2,SSize,C,false,0,1);
        Rect(SX,AB-(Small?4:7),BW,Small?4:7,Hex(0x64516e,.4f));
        Rect(SX,AB-(Small?4:7),BW*(I==0?1.f-Cooldown/2.4f:DisplayUltimate/100.f),Small?4:7,I==0?Cyan:Yellow);
    }
    Rect(AX+EWidth+Gap,AB-KH-11,1,KH+11,Hex(0x85798d,.53f));

    if(bDebugVisible)
    {
        const float DX=FMath::Max(14.f,W*.5f-190),DY=H*.24f,DW=FMath::Min(380.f,W-28);
        Rect(DX,DY,DW,223,Hex(0x110e1c,.96f));Rect(DX,DY,DW,2,Cyan);
        Text(TEXT("COMBAT / LIVE"),DX+16,DY+14,17,Cyan,true);
        Text(TEXT("F1 닫기 · ALT 누르고 마우스 조작"),DX+16,DY+43,11,Hex(0xa59bb3));
        Text(FString::Printf(TEXT("ATTACKS %d     HITS %d     CANCEL %d"),Player->AttackCount,Player->HitCount,Player->CancelCount),DX+16,DY+76,14,Ivory,true);
        Text(FString::Printf(TEXT("E %.1fs     Q %.0f%%     POSE %.0f Hz"),Cooldown,Player->UltimateCharge,Player->DisplayPoseFPS),DX+16,DY+104,14,Ivory,true);
        Text(FString::Printf(TEXT("%s    %.0f cm/s    %s"),Player->bRunning?TEXT("SPRINT"):TEXT("WALK"),Player->GetVelocity().Size2D(),Player->GetCharacterMovement()->IsFalling()?TEXT("AIR"):TEXT("GROUND")),DX+16,DY+132,13,Ivory,true);
        Rect(DX+16,DY+171,150,34,Hex(0x382944));Text(TEXT("HP −100"),DX+91,DY+179,14,Ivory,true,.5f);Region(TEXT("Damage"),DX+16,DY+171,150,34);
        Rect(DX+181,DY+171,150,34,Hex(0x382944));Text(TEXT("HP 회복"),DX+256,DY+179,14,Ivory,false,.5f);Region(TEXT("Heal"),DX+181,DY+171,150,34);
    }
    if(UGameplayStatics::IsGamePaused(this))
    {
        Rect(0,0,W,H,Hex(0x090610,.75f));
        const float PX=W*.5f-150,PY=H*.5f-163;
        Rect(PX,PY,300,326,Hex(0x160f23,.98f));Rect(PX,PY,300,2,Yellow);
        Text(TEXT("PAUSED"),W*.5f,PY+28,36,Ivory,true,.5f);
        Text(TEXT("전투 훈련 일시정지"),W*.5f,PY+79,12,Hex(0xa59bb3),false,.5f);
        const TCHAR* Labels[]={TEXT("계속하기"),TEXT("디버그 표시 / 숨김"),TEXT("훈련 다시 시작")};
        const FName IDs[]={TEXT("Resume"),TEXT("Debug"),TEXT("Restart")};
        for(int32 I=0;I<3;++I){Rect(PX+30,PY+117+I*49,240,40,I==0?Yellow:Hex(0x2b2138));Text(Labels[I],W*.5f,PY+129+I*49,13,I==0?Ink:Ivory,false,.5f);Region(IDs[I],PX+30,PY+117+I*49,240,40);}
        Text(TEXT("ESC 계속하기 · F1 디버그"),W*.5f,PY+287,11,Hex(0xa59bb3),false,.5f);
    }
}

bool APlaygroundHUD::HandleInterfaceClick(const FVector2D& Position)
{
    ACombatPlayerController* PC=Cast<ACombatPlayerController>(GetOwningPlayerController());
    APlaygroundCharacter* Player=Cast<APlaygroundCharacter>(GetOwningPawn());
    if(!PC||!Player)return false;
    const bool Paused=UGameplayStatics::IsGamePaused(this);
    for(const auto& Pair:InterfaceRegions)
    {
        if(!Pair.Value.IsInside(Position))continue;
        const FName ID=Pair.Key;
        if(Paused)
        {
            if(ID==TEXT("Resume")){PC->SetCombatPaused(false);return true;}
            if(ID==TEXT("Debug")){bDebugVisible=!bDebugVisible;PC->SetCombatPaused(false);return true;}
            if(ID==TEXT("Restart")){PC->SetCombatPaused(false);UGameplayStatics::OpenLevel(this,FName(*UGameplayStatics::GetCurrentLevelName(this,true)));return true;}
        }
        else
        {
            if(ID==TEXT("Menu")){PC->SetCombatPaused(true);return true;}
            if(ID==TEXT("Damage")){UGameplayStatics::ApplyDamage(Player,100,PC,this,nullptr);return true;}
            if(ID==TEXT("Heal")){Player->Health=Player->MaxHealth;return true;}
        }
    }
    return Paused;
}

void ACombatPlayerController::SetCombatPaused(bool bPaused)
{
    if(UGameplayStatics::IsGamePaused(this)==bPaused)return;
    FlushPressedKeys();
    if(APlaygroundCharacter* P=Cast<APlaygroundCharacter>(GetPawn()))
    {
        P->bRunning=false;
        P->GetCharacterMovement()->MaxWalkSpeed=280.f;
    }
    SetPause(bPaused);
    bShowMouseCursor=bPaused;
    if(bPaused)
    {
        FInputModeGameAndUI Mode;Mode.SetHideCursorDuringCapture(false);Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);SetInputMode(Mode);
    }
    else SetInputMode(FInputModeGameOnly());
}

bool ACombatPlayerController::InputKey(const FInputKeyEventArgs& Params)
{
    const bool Pressed=Params.Event==IE_Pressed;
    if(Params.Key==EKeys::Escape){if(Pressed)SetCombatPaused(!UGameplayStatics::IsGamePaused(this));return true;}
    if(Params.Key==EKeys::F1){if(Pressed)if(APlaygroundHUD* H=Cast<APlaygroundHUD>(GetHUD()))H->bDebugVisible=!H->bDebugVisible;return true;}
    if(Params.Key==EKeys::LeftAlt && !UGameplayStatics::IsGamePaused(this))
    {
        bShowMouseCursor=Params.Event!=IE_Released;
        if(bShowMouseCursor){FInputModeGameAndUI Mode;Mode.SetHideCursorDuringCapture(false);SetInputMode(Mode);}
        else SetInputMode(FInputModeGameOnly());
        return true;
    }
    if(Params.Key==EKeys::LeftMouseButton&&Pressed&&bShowMouseCursor)
    {
        float X,Y;if(GetMousePosition(X,Y))if(APlaygroundHUD* H=Cast<APlaygroundHUD>(GetHUD()))if(H->HandleInterfaceClick(FVector2D(X,Y)))return true;
    }
    if(UGameplayStatics::IsGamePaused(this))return true;
    if(bShowMouseCursor&&(Params.Key==EKeys::Mouse2D||Params.Key==EKeys::MouseX||Params.Key==EKeys::MouseY))return true;
    // Raw relative mouse input is never gated by attack, montage or hit-stop state.
    if(Params.Key==EKeys::MouseX){AddYawInput(Params.AmountDepressed*.12f);return true;}
    if(Params.Key==EKeys::MouseY){AddPitchInput(-Params.AmountDepressed*.12f);return true;}
    if(Pressed && !bShowMouseCursor && (Params.Key==EKeys::MouseScrollUp || Params.Key==EKeys::MouseScrollDown))
    {
        if(APawn* P=GetPawn())if(USpringArmComponent* Arm=P->FindComponentByClass<USpringArmComponent>())
            Arm->TargetArmLength=FMath::Clamp(Arm->TargetArmLength+(Params.Key==EKeys::MouseScrollUp?-40.f:40.f),150.f,1100.f);
        return true;
    }
    return Super::InputKey(Params);
}

void ACombatPlayerController::InjectMouseDelta(float X,float Y)
{
    InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::MouseX,IE_Axis,X,1));
    InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::MouseY,IE_Axis,Y,1));
}

#if WITH_EDITOR
namespace { TOptional<FInputChord> SavedStopChord; int32 ActiveHUDControllers=0; }
#endif
void ACombatPlayerController::BeginPlay()
{
    Super::BeginPlay();
    if(PlayerCameraManager){PlayerCameraManager->ViewPitchMin=-65.f;PlayerCameraManager->ViewPitchMax=65.f;}
#if WITH_EDITOR
    if(GetWorld()->WorldType==EWorldType::PIE && ActiveHUDControllers++==0)
    {
        // Only this play session: Escape reaches the pause menu; Shift+Escape still stops PIE.
        auto Stop=FInputBindingManager::Get().FindCommandInContext(TEXT("PlayWorld"),FName(TEXT("StopPlaySession")));
        if(Stop.IsValid() && *Stop->GetActiveChord(EMultipleKeyBindingIndex::Primary)==FInputChord(EKeys::Escape))
        {
            SavedStopChord=*Stop->GetActiveChord(EMultipleKeyBindingIndex::Primary);
            Stop->SetActiveChord(FInputChord(EKeys::Escape,true,false,false,false),EMultipleKeyBindingIndex::Primary);
        }
    }
#endif
}
void ACombatPlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
#if WITH_EDITOR
    if(GetWorld()->WorldType==EWorldType::PIE && --ActiveHUDControllers==0 && SavedStopChord.IsSet())
    {
        auto Stop=FInputBindingManager::Get().FindCommandInContext(TEXT("PlayWorld"),FName(TEXT("StopPlaySession")));
        if(Stop.IsValid())Stop->SetActiveChord(SavedStopChord.GetValue(),EMultipleKeyBindingIndex::Primary);
        SavedStopChord.Reset();
    }
#endif
    Super::EndPlay(EndPlayReason);
}
