import * as React from 'react';
import { motion, useAnimation } from 'motion/react';
import { cn } from '@/lib/utils';
import { useIsInView } from '@/hooks/useIsInView';
import { Slot } from '@/components/animate-ui/primitives/animate/slot';

const staticAnimations = {
  path: {
    initial: { pathLength: 1 },

    animate: {
      pathLength: [0.05, 1],
      transition: {
        duration: 0.8,
        ease: 'easeInOut',
      },
    }
  },

  'path-loop': {
    initial: { pathLength: 1 },

    animate: {
      pathLength: [1, 0.05, 1],
      transition: {
        duration: 1.6,
        ease: 'easeInOut',
      },
    }
  }
};

const AnimateIconContext = React.createContext(null);

function useAnimateIconContext() {
  const context = React.useContext(AnimateIconContext);
  if (!context)
    return {
      controls: undefined,
      animation: 'default',
      loop: undefined,
      loopDelay: undefined,
      active: undefined,
      animate: undefined,
      initialOnAnimateEnd: undefined,
      completeOnStop: undefined,
      persistOnAnimateEnd: undefined,
      delay: undefined,
      speedMultiplier: 0.7,
    };
  return context;
}

function composeEventHandlers(theirs, ours) {
  return (event) => {
    theirs?.(event);
    ours?.(event);
  };
}

function AnimateIcon({
  asChild = false,
  animate = false,
  animateOnHover = false,
  animateOnTap = false,
  animateOnView = false,
  animateOnViewMargin = '0px',
  animateOnViewOnce = true,
  animation = 'default',
  loop = false,
  loopDelay = 0,
  initialOnAnimateEnd = false,
  completeOnStop = false,
  persistOnAnimateEnd = false,
  delay = 0,
  children,
  ...props
}) {
  const controls = useAnimation();

  const [localAnimate, setLocalAnimate] = React.useState(() => {
    if (animate === undefined || animate === false) return false;
    return delay <= 0;
  });
  const [currentAnimation, setCurrentAnimation] = React.useState(typeof animate === 'string' ? animate : animation);
  const [status, setStatus] = React.useState('initial');

  const delayRef = React.useRef(null);
  const loopDelayRef = React.useRef(null);
  const isAnimateInProgressRef = React.useRef(false);
  const animateEndPromiseRef = React.useRef(null);
  const resolveAnimateEndRef = React.useRef(null);
  const activeRef = React.useRef(localAnimate);

  const runGenRef = React.useRef(0);
  const cancelledRef = React.useRef(false);

  const bumpGeneration = React.useCallback(() => {
    runGenRef.current++;
  }, []);

  const startAnimation = React.useCallback((trigger) => {
    const next = typeof trigger === 'string' ? trigger : animation;
    bumpGeneration();
    if (delayRef.current) {
      clearTimeout(delayRef.current);
      delayRef.current = null;
    }
    setCurrentAnimation(next);
    if (delay > 0) {
      setLocalAnimate(false);
      delayRef.current = setTimeout(() => {
        setLocalAnimate(true);
      }, delay);
    } else {
      setLocalAnimate(true);
    }
  }, [animation, delay, bumpGeneration]);

  const stopAnimation = React.useCallback(() => {
    bumpGeneration();
    if (delayRef.current) {
      clearTimeout(delayRef.current);
      delayRef.current = null;
    }
    if (loopDelayRef.current) {
      clearTimeout(loopDelayRef.current);
      loopDelayRef.current = null;
    }
    setLocalAnimate(false);
  }, [bumpGeneration]);

  React.useEffect(() => {
    activeRef.current = localAnimate;
  }, [localAnimate]);

  React.useEffect(() => {
    if (animate === undefined) return;
    setCurrentAnimation(typeof animate === 'string' ? animate : animation);
    if (animate) startAnimation(animate);
    else stopAnimation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [animate]);

  React.useEffect(() => {
    return () => {
      if (delayRef.current) clearTimeout(delayRef.current);
      if (loopDelayRef.current) clearTimeout(loopDelayRef.current);
    };
  }, []);

  const viewOuterRef = React.useRef(null);
  const { ref: inViewRef, isInView } = useIsInView(viewOuterRef, {
    inView: !!animateOnView,
    inViewOnce: animateOnViewOnce,
    inViewMargin: animateOnViewMargin,
  });

  const startAnim = React.useCallback(async (anim, method = 'start') => {
    try {
      await controls[method](anim);
      setStatus(anim);
    } catch {
      return;
    }
  }, [controls]);

  React.useEffect(() => {
    if (!animateOnView) return;
    if (isInView) startAnimation(animateOnView);
    else stopAnimation();
  }, [isInView, animateOnView, startAnimation, stopAnimation]);

  React.useEffect(() => {
    const gen = ++runGenRef.current;
    cancelledRef.current = false;

    async function run() {
      if (cancelledRef.current || gen !== runGenRef.current) {
        await startAnim('initial');
        return;
      }

      if (!localAnimate) {
        if (
          completeOnStop &&
          isAnimateInProgressRef.current &&
          animateEndPromiseRef.current
        ) {
          try {
            await animateEndPromiseRef.current;
          } catch {
            // noop
          }
        }
        if (!persistOnAnimateEnd) {
          if (cancelledRef.current || gen !== runGenRef.current) {
            await startAnim('initial');
            return;
          }
          await startAnim('initial');
        }
        return;
      }

      if (loop) {
        if (cancelledRef.current || gen !== runGenRef.current) {
          await startAnim('initial');
          return;
        }
        await startAnim('initial', 'set');
      }

      isAnimateInProgressRef.current = true;
      animateEndPromiseRef.current = new Promise((resolve) => {
        resolveAnimateEndRef.current = resolve;
      });

      if (cancelledRef.current || gen !== runGenRef.current) {
        isAnimateInProgressRef.current = false;
        resolveAnimateEndRef.current?.();
        resolveAnimateEndRef.current = null;
        animateEndPromiseRef.current = null;
        await startAnim('initial');
        return;
      }

      await startAnim('animate');

      if (cancelledRef.current || gen !== runGenRef.current) {
        isAnimateInProgressRef.current = false;
        resolveAnimateEndRef.current?.();
        resolveAnimateEndRef.current = null;
        animateEndPromiseRef.current = null;
        await startAnim('initial');
        return;
      }

      isAnimateInProgressRef.current = false;
      resolveAnimateEndRef.current?.();
      resolveAnimateEndRef.current = null;
      animateEndPromiseRef.current = null;

      if (initialOnAnimateEnd) {
        if (cancelledRef.current || gen !== runGenRef.current) {
          await startAnim('initial');
          return;
        }
        await startAnim('initial', 'set');
      }

      if (loop) {
        if (loopDelay > 0) {
          await new Promise((resolve) => {
            loopDelayRef.current = setTimeout(() => {
              loopDelayRef.current = null;
              resolve();
            }, loopDelay);
          });

          if (cancelledRef.current || gen !== runGenRef.current) {
            await startAnim('initial');
            return;
          }
          if (!activeRef.current) {
            if (status !== 'initial' && !persistOnAnimateEnd)
              await startAnim('initial');
            return;
          }
        } else {
          if (!activeRef.current) {
            if (status !== 'initial' && !persistOnAnimateEnd)
              await startAnim('initial');
            return;
          }
        }
        if (cancelledRef.current || gen !== runGenRef.current) {
          await startAnim('initial');
          return;
        }
        await run();
      }
    }

    void run();

    return () => {
      cancelledRef.current = true;
      if (delayRef.current) {
        clearTimeout(delayRef.current);
        delayRef.current = null;
      }
      if (loopDelayRef.current) {
        clearTimeout(loopDelayRef.current);
        loopDelayRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [localAnimate, controls]);

  const childProps = (React.isValidElement(children) ? (children).props : {});

  const handleMouseEnter = composeEventHandlers(childProps.onMouseEnter, () => {
    if (animateOnHover) startAnimation(animateOnHover);
  });

  const handleMouseLeave = composeEventHandlers(childProps.onMouseLeave, () => {
    if (animateOnHover || animateOnTap) stopAnimation();
  });

  const handlePointerDown = composeEventHandlers(childProps.onPointerDown, () => {
    if (animateOnTap) startAnimation(animateOnTap);
  });

  const handlePointerUp = composeEventHandlers(childProps.onPointerUp, () => {
    if (animateOnTap) stopAnimation();
  });

  const content = asChild ? (
    <Slot
      ref={inViewRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      {...props}>
      {children}
    </Slot>
  ) : (
    <motion.span
      ref={inViewRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      {...props}>
      {children}
    </motion.span>
  );

  const parentContext = React.useContext(AnimateIconContext);
  const inheritedSpeedMultiplier = parentContext?.speedMultiplier;

  const contextValue = React.useMemo(() => {
    const value = {
      controls,
      animation: currentAnimation,
      loop,
      loopDelay,
      active: localAnimate,
      animate,
      initialOnAnimateEnd,
      completeOnStop,
      delay,
    };
    if (inheritedSpeedMultiplier !== undefined) {
      value.speedMultiplier = inheritedSpeedMultiplier;
    }
    return value;
  }, [controls, currentAnimation, loop, loopDelay, localAnimate, animate, initialOnAnimateEnd, completeOnStop, delay, inheritedSpeedMultiplier]);

  return (
    <AnimateIconContext.Provider value={contextValue}>
      {content}
    </AnimateIconContext.Provider>
  );
}

const pathClassName =
  "[&_[stroke-dasharray='1px_1px']]:![stroke-dasharray:1px_0px]";

function IconWrapper(
  {
    size = 28,
    animation: animationProp,
    animate,
    animateOnHover,
    animateOnTap,
    animateOnView,
    animateOnViewMargin,
    animateOnViewOnce,
    icon: IconComponent,
    loop,
    loopDelay,
    persistOnAnimateEnd,
    initialOnAnimateEnd,
    delay,
    completeOnStop,
    speedMultiplier = 0.7,
    className,
    ...props
  }
) {
  const context = React.useContext(AnimateIconContext);

  if (context) {
    const {
      controls,
      animation: parentAnimation,
      loop: parentLoop,
      loopDelay: parentLoopDelay,
      active: parentActive,
      animate: parentAnimate,
      persistOnAnimateEnd: parentPersistOnAnimateEnd,
      initialOnAnimateEnd: parentInitialOnAnimateEnd,
      delay: parentDelay,
      completeOnStop: parentCompleteOnStop,
      speedMultiplier: parentSpeedMultiplier,
    } = context;

    const hasAnimationOverrides =
      animate !== undefined ||
      animateOnHover !== undefined ||
      animateOnTap !== undefined ||
      animateOnView !== undefined ||
      loop !== undefined ||
      loopDelay !== undefined ||
      initialOnAnimateEnd !== undefined ||
      persistOnAnimateEnd !== undefined ||
      delay !== undefined ||
      completeOnStop !== undefined;

    const hasSpeedMultiplierOverride = speedMultiplier !== undefined;

    if (hasSpeedMultiplierOverride && !hasAnimationOverrides) {
      const animationToUse = animationProp ?? parentAnimation;
      const finalSpeedMultiplier = speedMultiplier ?? parentSpeedMultiplier ?? 0.7;

      return (
        <AnimateIconContext.Provider
          value={{
            controls,
            animation: animationToUse,
            loop: parentLoop,
            loopDelay: parentLoopDelay,
            active: parentActive,
            animate: parentAnimate,
            initialOnAnimateEnd: parentInitialOnAnimateEnd,
            delay: parentDelay,
            completeOnStop: parentCompleteOnStop,
            speedMultiplier: finalSpeedMultiplier,
          }}>
          <IconComponent
            size={size}
            className={cn(
              className,
              (animationToUse === 'path' || animationToUse === 'path-loop') &&
                pathClassName
            )}
            {...props} />
        </AnimateIconContext.Provider>
      );
    }

    if (hasAnimationOverrides) {
      const inheritedAnimate = parentActive
        ? (animationProp ?? parentAnimation ?? 'default')
        : false;

      const finalAnimate = (animate ??
        parentAnimate ?? inheritedAnimate);

      const finalSpeedMultiplier = speedMultiplier ?? parentSpeedMultiplier ?? 0.7;
      
      return (
        <AnimateIconContext.Provider
          value={{
            ...context,
            speedMultiplier: finalSpeedMultiplier,
          }}>
          <AnimateIcon
            animate={finalAnimate}
            animateOnHover={animateOnHover}
            animateOnTap={animateOnTap}
            animateOnView={animateOnView}
            animateOnViewMargin={animateOnViewMargin}
            animateOnViewOnce={animateOnViewOnce}
            animation={animationProp ?? parentAnimation}
            loop={loop ?? parentLoop}
            loopDelay={loopDelay ?? parentLoopDelay}
            persistOnAnimateEnd={persistOnAnimateEnd ?? parentPersistOnAnimateEnd}
            initialOnAnimateEnd={initialOnAnimateEnd ?? parentInitialOnAnimateEnd}
            delay={delay ?? parentDelay}
            completeOnStop={completeOnStop ?? parentCompleteOnStop}
            asChild>
            <IconComponent
              size={size}
              className={cn(className, ((animationProp ?? parentAnimation) === 'path' ||
                (animationProp ?? parentAnimation) === 'path-loop') &&
                pathClassName)}
              {...props} />
          </AnimateIcon>
        </AnimateIconContext.Provider>
      );
    }

    const animationToUse = animationProp ?? parentAnimation;
    const loopToUse = parentLoop;
    const loopDelayToUse = parentLoopDelay;
    const finalSpeedMultiplier = speedMultiplier ?? parentSpeedMultiplier ?? 0.7;

    return (
      <AnimateIconContext.Provider
        value={{
          controls,
          animation: animationToUse,
          loop: loopToUse,
          loopDelay: loopDelayToUse,
          active: parentActive,
          animate: parentAnimate,
          initialOnAnimateEnd: parentInitialOnAnimateEnd,
          delay: parentDelay,
          completeOnStop: parentCompleteOnStop,
          speedMultiplier: finalSpeedMultiplier,
        }}>
        <IconComponent
          size={size}
          className={cn(
            className,
            (animationToUse === 'path' || animationToUse === 'path-loop') &&
              pathClassName
          )}
          {...props} />
      </AnimateIconContext.Provider>
    );
  }

  if (
    animate !== undefined ||
    animateOnHover !== undefined ||
    animateOnTap !== undefined ||
    animateOnView !== undefined ||
    animationProp !== undefined ||
    speedMultiplier !== undefined
  ) {
    return (
      <AnimateIconContext.Provider
        value={{
          controls: undefined,
          animation: animationProp,
          loop,
          loopDelay,
          active: undefined,
          animate,
          initialOnAnimateEnd,
          delay,
          completeOnStop,
          speedMultiplier: speedMultiplier ?? 0.7,
        }}>
        <AnimateIcon
          animate={animate}
          animateOnHover={animateOnHover}
          animateOnTap={animateOnTap}
          animateOnView={animateOnView}
          animateOnViewMargin={animateOnViewMargin}
          animateOnViewOnce={animateOnViewOnce}
          animation={animationProp}
          loop={loop}
          loopDelay={loopDelay}
          delay={delay}
          completeOnStop={completeOnStop}
          asChild>
          <IconComponent
            size={size}
            className={cn(className, (animationProp === 'path' || animationProp === 'path-loop') &&
              pathClassName)}
            {...props} />
        </AnimateIcon>
      </AnimateIconContext.Provider>
    );
  }

  return (
    <IconComponent
      size={size}
      className={cn(className, (animationProp === 'path' || animationProp === 'path-loop') &&
        pathClassName)}
      {...props} />
  );
}

function getVariants(animations) {
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const { animation: animationType, speedMultiplier } = useAnimateIconContext();

  let result;

  if (animationType in staticAnimations) {
    const variant = staticAnimations[animationType];
    result = {};
    for (const key in animations.default) {
      if (
        (animationType === 'path' || animationType === 'path-loop') &&
        key.includes('group')
      )
        continue;
      result[key] = variant;
    }
  } else {
    result = (animations[animationType]) ?? animations.default;
  }

  if (speedMultiplier !== undefined && speedMultiplier !== 1) {
    result = adjustAnimationSpeed(result, speedMultiplier);
  }

  return result;
}

function adjustAnimationSpeed(animations, multiplier) {
  if (!animations || typeof animations !== 'object') {
    return animations;
  }

  if (Array.isArray(animations)) {
    return animations.map(item => adjustAnimationSpeed(item, multiplier));
  }

  const adjusted = {};
  for (const key in animations) {
    const anim = animations[key];
    
    if (anim === null || anim === undefined) {
      adjusted[key] = anim;
      continue;
    }

    if (typeof anim === 'object') {
      if ('initial' in anim || 'animate' in anim) {
        adjusted[key] = {
          ...anim,
        };
        
        if (anim.initial && typeof anim.initial === 'object' && anim.initial.transition) {
          adjusted[key].initial = {
            ...anim.initial,
            transition: adjustTransition(anim.initial.transition, multiplier),
          };
        }
        
        if (anim.animate && typeof anim.animate === 'object') {
          adjusted[key].animate = { ...anim.animate };
          
          if (anim.animate.transition) {
            adjusted[key].animate.transition = adjustTransition(anim.animate.transition, multiplier);
          }
        }
      }
      else if (anim.transition) {
        adjusted[key] = {
          ...anim,
          transition: adjustTransition(anim.transition, multiplier),
        };
      }
      else {
        adjusted[key] = adjustAnimationSpeed(anim, multiplier);
      }
    } else {
      adjusted[key] = anim;
    }
  }
  return adjusted;
}

function adjustTransition(transition, multiplier) {
  if (!transition) return transition;
  if (typeof transition === 'object') {
    const adjusted = { ...transition };
    if (typeof transition.duration === 'number') {
      adjusted.duration = transition.duration * multiplier;
    }
    if (typeof transition.delay === 'number') {
      adjusted.delay = transition.delay * multiplier;
    }
    return adjusted;
  }
  return transition;
}

export { pathClassName, staticAnimations, AnimateIcon, IconWrapper, useAnimateIconContext, getVariants };
