import React from "react"
import { motion } from "motion/react"
import { getVariants, useAnimateIconContext, IconWrapper } from "@/components/animate-ui/icons/icon"

const animations = {
  default: (() => {
    const animation = {}
    for (let i = 0; i <= 5; i++) {
      animation[`path${i + 1}`] = {
        initial: { pathLength: 1, opacity: 1 },
        animate: {
          pathLength: [0, 1],
          opacity: [0, 1],
          transition: {
            duration: 0.6,
            delay: i * 0.12,
            ease: [0.4, 0, 0.2, 1],
          },
        },
      }
    }
    return animation
  })(),
  "draw-stroke": (() => {
    const animation = {}
    for (let i = 0; i <= 5; i++) {
      animation[`path${i + 1}`] = {
        initial: { pathLength: 1, opacity: 1 },
        animate: {
          pathLength: [0, 1],
          opacity: [0, 1],
          transition: {
            duration: 0.8,
            delay: i * 0.12,
            ease: [0.4, 0, 0.2, 1],
          },
        },
      }
    }
    return animation
  })(),
  "scale-group": (() => {
    const animation = {}
    animation.path1 = {
      initial: { scale: 1, opacity: 1 },
      animate: {
        scale: [0.85, 1.2, 1],
        opacity: [1, 1],
        transition: {
          duration: 0.8,
          delay: 0,
          ease: [0.34, 1.56, 0.64, 1],
        },
      },
    }
    animation.path2 = {
      initial: { scale: 1, opacity: 1 },
      animate: {
        scale: [0.85, 1.2, 1],
        opacity: [1, 1],
        transition: {
          duration: 0.8,
          delay: 0,
          ease: [0.34, 1.56, 0.64, 1],
        },
      },
    }
    animation.path3 = {
      initial: { scale: 1, opacity: 1 },
      animate: {
        scale: [0.85, 1.2, 1],
        opacity: [1, 1],
        transition: {
          duration: 0.8,
          delay: 0.12,
          ease: [0.34, 1.56, 0.64, 1],
        },
      },
    }
    animation.path4 = {
      initial: { scale: 1, opacity: 1 },
      animate: {
        scale: [0.85, 1.2, 1],
        opacity: [1, 1],
        transition: {
          duration: 0.8,
          delay: 0.12,
          ease: [0.34, 1.56, 0.64, 1],
        },
      },
    }
    animation.path5 = {
      initial: { scale: 1, opacity: 1 },
      animate: {
        scale: [0.85, 1.2, 1],
        opacity: [1, 1],
        transition: {
          duration: 0.8,
          delay: 0.24,
          ease: [0.34, 1.56, 0.64, 1],
        },
      },
    }
    animation.path6 = {
      initial: { scale: 1, opacity: 1 },
      animate: {
        scale: [0.85, 1.2, 1],
        opacity: [1, 1],
        transition: {
          duration: 0.8,
          delay: 0.24,
          ease: [0.34, 1.56, 0.64, 1],
        },
      },
    }
    return animation
  })(),
  bounce: {
    group: {
      initial: { y: 0 },
      animate: {
        y: [0, -10, 0, -5, 0],
        transition: {
          duration: 0.7,
          ease: [0.68, -0.55, 0.265, 1.55],
        },
      },
    },
    path1: {},
    path2: {},
    path3: {},
    path4: {},
    path5: {},
    path6: {},
  },
}

function IconComponent({ size, ...props }) {
  const { controls, animation: animationType } = useAnimateIconContext()
  const variants = getVariants(animations)
  const variant = animationType || "draw-stroke"

  if (variant === "draw-stroke") {
    return (
      <motion.svg
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial="initial"
        animate={controls}
        {...props}
      >
        <motion.path d="m5 8 6 6" variants={variants.path1} initial="initial" animate={controls} />
        <motion.path d="m4 14 6-6 2-3" variants={variants.path2} initial="initial" animate={controls} />
        <motion.path d="M2 5h12" variants={variants.path3} initial="initial" animate={controls} />
        <motion.path d="M7 2h1" variants={variants.path4} initial="initial" animate={controls} />
        <motion.path d="m22 22-5-10-5 10" variants={variants.path5} initial="initial" animate={controls} />
        <motion.path d="M14 18h6" variants={variants.path6} initial="initial" animate={controls} />
      </motion.svg>
    )
  }

  if (variant === "scale-group") {
    return (
      <motion.svg
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial="initial"
        animate={controls}
        {...props}
      >
        <motion.path
          d="m5 8 6 6"
          variants={variants.path1}
          initial="initial"
          animate={controls}
          style={{ originX: 0.5, originY: 0.5 }}
        />
        <motion.path
          d="m4 14 6-6 2-3"
          variants={variants.path2}
          initial="initial"
          animate={controls}
          style={{ originX: 0.5, originY: 0.5 }}
        />
        <motion.path
          d="M2 5h12"
          variants={variants.path3}
          initial="initial"
          animate={controls}
          style={{ originX: 0.5, originY: 0.5 }}
        />
        <motion.path
          d="M7 2h1"
          variants={variants.path4}
          initial="initial"
          animate={controls}
          style={{ originX: 0.5, originY: 0.5 }}
        />
        <motion.path
          d="m22 22-5-10-5 10"
          variants={variants.path5}
          initial="initial"
          animate={controls}
          style={{ originX: 0.5, originY: 0.5 }}
        />
        <motion.path
          d="M14 18h6"
          variants={variants.path6}
          initial="initial"
          animate={controls}
          style={{ originX: 0.5, originY: 0.5 }}
        />
      </motion.svg>
    )
  }

  if (variant === "bounce") {
    return (
      <motion.svg
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial="initial"
        animate={controls}
        variants={variants.group}
        {...props}
      >
        <path d="m5 8 6 6" />
        <path d="m4 14 6-6 2-3" />
        <path d="M2 5h12" />
        <path d="M7 2h1" />
        <path d="m22 22-5-10-5 10" />
        <path d="M14 18h6" />
      </motion.svg>
    )
  }

  return (
    <motion.svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      initial="initial"
      animate={controls}
      {...props}
    >
      <motion.path d="m5 8 6 6" variants={variants.path1} initial="initial" animate={controls} />
      <motion.path d="m4 14 6-6 2-3" variants={variants.path2} initial="initial" animate={controls} />
      <motion.path d="M2 5h12" variants={variants.path3} initial="initial" animate={controls} />
      <motion.path d="M7 2h1" variants={variants.path4} initial="initial" animate={controls} />
      <motion.path d="m22 22-5-10-5 10" variants={variants.path5} initial="initial" animate={controls} />
      <motion.path d="M14 18h6" variants={variants.path6} initial="initial" animate={controls} />
    </motion.svg>
  )
}

function LanguagesIcon(props) {
  return <IconWrapper icon={IconComponent} {...props} />
}

export { animations, LanguagesIcon, LanguagesIcon as LanguagesIconIcon }
