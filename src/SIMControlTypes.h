#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>

NS_ASSUME_NONNULL_BEGIN

@interface SIMControlItem : NSObject
@property(nonatomic) NSInteger slot;
@property(nonatomic,copy) NSString *name;
@property(nonatomic) BOOL enabled;
@property(nonatomic) BOOL available;
@end

typedef void (^SIMControlReadCompletion)(NSArray<SIMControlItem *> *items, NSString * _Nullable error);
typedef void (^SIMControlActionCompletion)(BOOL accepted, NSString * _Nullable error);

@interface SIMControlService : NSObject
- (void)readItems:(SIMControlReadCompletion)completion;
- (void)setItem:(SIMControlItem *)item enabled:(BOOL)enabled completion:(SIMControlActionCompletion)completion;
@end

@interface SIMControlRow : UIControl
- (void)updateWithItem:(SIMControlItem *)item busy:(BOOL)busy;
@end

NS_ASSUME_NONNULL_END
